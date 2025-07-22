# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import sqlite3
import json
import sys
import os
import uuid

# 프로젝트 루트 경로를 sys.path에 추가
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from retriever.retriever import make_retriever, parse_search_results, embeddings
from reranker.reranking import reranking
from llm.gemini.perform_inference import llmResponse

# FastAPI 앱 생성
app = FastAPI(title="창원대학교 공지사항 검색 API", version="1.0.0")

# CORS 설정 - 모든 origin 허용 (프로덕션에서는 특정 도메인만 허용하도록 수정 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 Retriever 선언
denseRetriever = None
sparseRetriever = None

# 데이터베이스 설정
DB_PATH = os.path.join(PROJECT_ROOT, "chats.db")

def init_database():
    """SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 채팅방 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chatrooms (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 메시지 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            chatroom_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chatroom_id) REFERENCES chatrooms (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 요청/응답 모델 정의
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    chatroom_id: Optional[str] = None

class ChatRoom(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class Message(BaseModel):
    id: str
    chatroom_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]]
    created_at: str

class SearchResult(BaseModel):
    content: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    llm_response: str
    total_results: int

# 서버 시작 시 Retriever 초기화
@app.on_event("startup")
async def startup_event():
    global denseRetriever, sparseRetriever
    print("데이터베이스를 초기화하는 중입니다...")
    init_database()
    print("데이터베이스 초기화 완료!")
    
    print("검색 시스템을 초기화하는 중입니다...")
    denseRetriever, sparseRetriever = make_retriever()
    print("검색 시스템 초기화 완료!")

def format_results_to_xml(results):
    """
    검색 결과를 XML 형태의 문자열로 포맷팅
    """
    xml_parts = ['<SearchResults>']
    
    for idx, (content, score, metadata) in enumerate(results, 1):
        xml_parts.append(f'  <Document rank="{idx}">')
        xml_parts.append(f'    <RelevanceScore>{score:.4f}</RelevanceScore>')
        xml_parts.append(f'    <Metadata>')
        xml_parts.append(f'      <Number>{metadata.get("number", "N/A")}</Number>')
        xml_parts.append(f'      <Author>{metadata.get("author", "N/A")}</Author>')
        xml_parts.append(f'      <Date>{metadata.get("date", "N/A")}</Date>')
        xml_parts.append(f'      <Views>{metadata.get("views", "0")}</Views>')
        xml_parts.append(f'      <URL>{metadata.get("url", "N/A")}</URL>')
        xml_parts.append(f'    </Metadata>')
        xml_parts.append(f'    <Content><![CDATA[{content}]]></Content>')
        xml_parts.append(f'  </Document>')
    
    xml_parts.append('</SearchResults>')
    
    return '\n'.join(xml_parts)

def search_and_rerank(query: str, top_k: int = 5):
    """
    쿼리를 받아서 검색 및 리랭킹을 수행하는 함수
    """
    global denseRetriever, sparseRetriever
    
    # 쿼리 임베딩
    query_embed = embeddings.embed_query(query)
    
    # 밀집 검색과 희소 검색 수행
    denseResult = denseRetriever.similarity_search_with_score_by_vector(query_embed, 50)
    sparseResult = sparseRetriever.search_with_score(query)
    
    # 결과 파싱
    all_results = parse_search_results(denseResult, sparseResult)
    
    # 리랭킹을 위한 형식 변환
    rerank_input = [[query, result[0], result[2]] for result in all_results]
    
    # 리랭킹 수행
    reranked_results = reranking(rerank_input)
    
    return reranked_results[:top_k]

@app.get("/")
async def root():
    return {"message": "창원대학교 공지사항 검색 API", "status": "running"}

# 채팅방 관련 API
@app.get("/chatrooms", response_model=List[ChatRoom])
async def get_chatrooms():
    """모든 채팅방 목록 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM chatrooms ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.post("/chatrooms", response_model=ChatRoom)
async def create_chatroom(title: str = "새 대화"):
    """새 채팅방 생성"""
    chatroom_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO chatrooms (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (chatroom_id, title, now, now)
    )
    conn.commit()
    conn.close()
    
    return ChatRoom(id=chatroom_id, title=title, created_at=now, updated_at=now)

@app.put("/chatrooms/{chatroom_id}/title")
async def update_chatroom_title(chatroom_id: str, title: str):
    """채팅방 제목 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE chatrooms SET title = ?, updated_at = ? WHERE id = ?",
        (title, datetime.now().isoformat(), chatroom_id)
    )
    
    conn.commit()
    conn.close()
    
    return {"message": "채팅방 제목이 업데이트되었습니다."}

@app.get("/chatrooms/{chatroom_id}/messages", response_model=List[Message])
async def get_messages(chatroom_id: str):
    """특정 채팅방의 메시지 목록 조회"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM messages WHERE chatroom_id = ? ORDER BY created_at ASC",
        (chatroom_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    
    messages = []
    for row in rows:
        msg = dict(row)
        if msg['sources']:
            msg['sources'] = json.loads(msg['sources'])
        messages.append(msg)
    
    return messages

@app.delete("/chatrooms/{chatroom_id}")
async def delete_chatroom(chatroom_id: str):
    """채팅방 삭제"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 메시지 먼저 삭제
    cursor.execute("DELETE FROM messages WHERE chatroom_id = ?", (chatroom_id,))
    # 채팅방 삭제
    cursor.execute("DELETE FROM chatrooms WHERE id = ?", (chatroom_id,))
    
    conn.commit()
    conn.close()
    
    return {"message": "채팅방이 삭제되었습니다."}

@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    검색 API 엔드포인트
    """
    try:
        # 검색 수행
        results = search_and_rerank(request.query, request.top_k)
        
        # 결과를 XML 형태로 포맷팅
        xml_formatted_results = format_results_to_xml(results)
        
        # LLM 응답 생성
        llm_answer = llmResponse(request.query, xml_formatted_results)
        
        # 결과 포맷팅
        formatted_results = []
        for content, score, metadata in results:
            formatted_results.append(SearchResult(
                content=content,
                score=score,
                metadata=metadata
            ))
        
        # 채팅방이 지정된 경우 메시지 저장
        if request.chatroom_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            # 사용자 메시지 저장
            user_msg_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO messages (id, chatroom_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (user_msg_id, request.chatroom_id, "user", request.query, None, now)
            )
            
            # AI 응답 저장
            ai_msg_id = str(uuid.uuid4())
            sources_json = json.dumps([{
                'content': r.content,
                'score': r.score,
                'metadata': r.metadata
            } for r in formatted_results])
            
            cursor.execute(
                "INSERT INTO messages (id, chatroom_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (ai_msg_id, request.chatroom_id, "assistant", llm_answer, sources_json, now)
            )
            
            # 채팅방 업데이트 시간 갱신
            cursor.execute(
                "UPDATE chatrooms SET updated_at = ? WHERE id = ?",
                (now, request.chatroom_id)
            )
            
            conn.commit()
            conn.close()
        
        return SearchResponse(
            query=request.query,
            results=formatted_results,
            llm_response=llm_answer,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "healthy", "retrievers_loaded": denseRetriever is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=22222)