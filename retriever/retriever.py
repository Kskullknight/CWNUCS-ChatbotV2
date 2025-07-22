from dotenv import load_dotenv
load_dotenv()

import glob, mysql.connector, faiss, pickle
from langchain_community.vectorstores import FAISS
from langchain_teddynote.retrievers import KiwiBM25Retriever
from langchain_upstage import UpstageEmbeddings
import sys
import os

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from reranker.reranking import reranking

embeddings = UpstageEmbeddings(model="solar-embedding-1-large")

def make_retriever():
    global embeddings

    # 절대경로로 변경 (vectorStore는 retriever 폴더 안에 있음)
    vector_store_path = os.path.join(PROJECT_ROOT, "retriever", "vectorStore", "cwnu_vector.pkl")
    with open(vector_store_path, 'rb') as file:
        cwnu_pairs = pickle.load(file)
        """[원몬문장, [임베딩벡터], 논문의 ID값]"""

        s_v_pair = [[d[0], d[1]] for d in cwnu_pairs]
        meta_data = [d[2] for d in cwnu_pairs]

        vector_db_cwnu = FAISS.from_embeddings(s_v_pair, embeddings, metadatas=meta_data)
        
        texts = [d[0] for d in cwnu_pairs]
        meta_data = [d[2] for d in cwnu_pairs]

        bm25_Retriever = KiwiBM25Retriever.from_texts(
            texts,
            metadatas = meta_data
        )

        bm25_Retriever.k = 50

        return vector_db_cwnu, bm25_Retriever

def parse_search_results(dense_results, sparse_results):
    """
    밀집 검색과 희소 검색 결과를 통일된 형식으로 파싱
    
    Returns:
        list: [[content, score, metadata], ...]
    """
    parsed_results = []
    
    # 밀집 검색 결과 파싱 (튜플 형식)
    for doc, score in dense_results:
        parsed_results.append([
            doc.page_content,
            score,
            doc.metadata,
            "dense"  # 검색 타입 표시
        ])
    
    # 희소 검색 결과 파싱 (딕셔너리 형식)
    for result in sparse_results:
        parsed_results.append([
            result.page_content,
            result.metadata.get('score', 0),
            {k: v for k, v in result.metadata.items() if k != 'score'},
            "sparse"  # 검색 타입 표시
        ])
    
    return parsed_results


# 테스트 코드는 직접 실행할 때만 동작하도록 수정
if __name__ == "__main__":
    denseRetriever, sparseRetriever = make_retriever()

    query = "수강신청에 대해 조사해주세요"
    query_embed = embeddings.embed_query(query)

    denseResult = denseRetriever.similarity_search_with_score_by_vector(query_embed, 50)
    sparseResult = sparseRetriever.search_with_score(query)

    # 결과 파싱
    parsed_dense = parse_search_results(denseResult, [])
    parsed_sparse = parse_search_results([], sparseResult)

    print("밀집 검색 결과 (파싱됨) ->")
    print(parsed_dense[0] if parsed_dense else "결과 없음")

    print("\n희소 검색 결과 (파싱됨) ->")
    print(parsed_sparse[0] if parsed_sparse else "결과 없음")

    # 모든 결과 합치기
    all_results = parse_search_results(denseResult, sparseResult)
    print(f"\n전체 결과 개수: {len(all_results)}")

    rerank_input = [[query, result[0], result[2]] for result in all_results]

    # reranking 수행
    print("\nReranking 수행 중...")
    reranked_results = reranking(rerank_input)

    print(f"\nReranking 완료! 상위 5개 결과:")
    for i, result in enumerate(reranked_results[:5]):
        print(f"\n{i+1}. 점수: {result[1]:.4f}")
        print(f"   메타데이터: {result[2]}")
        print(f"   내용 미리보기: {result[0][:100]}...")










