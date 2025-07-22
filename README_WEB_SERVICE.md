# 창원대학교 공지사항 검색 웹 서비스

## 프로젝트 구조
- `search_api.py`: FastAPI 백엔드 서버
- `web_service/`: React 프론트엔드 애플리케이션

## 필요한 패키지 설치

### 백엔드 (FastAPI)
```bash
pip install fastapi uvicorn
```

### 프론트엔드 (React)
프론트엔드 패키지는 이미 설치되어 있습니다.

## 실행 방법

### 1. 백엔드 서버 실행
터미널 1에서:
```bash
cd /home/jinsoo/Desktop/MyChatbot
python3 search_api.py
```
서버가 http://localhost:8000 에서 실행됩니다.

### 2. 프론트엔드 실행
터미널 2에서:
```bash
cd /home/jinsoo/Desktop/MyChatbot/web_service
npm start
```
웹 애플리케이션이 http://localhost:3000 에서 실행됩니다.

## 사용 방법
1. 웹 브라우저에서 http://localhost:3000 접속
2. 검색창에 질문 입력 (예: "수강신청", "졸업요건", "장학금")
3. 검색 버튼 클릭
4. AI 답변과 관련 공지사항 확인

## API 엔드포인트
- `GET /`: API 상태 확인
- `POST /search`: 검색 수행
- `GET /health`: 헬스 체크

## 특징
- 밀집 검색과 희소 검색을 결합한 하이브리드 검색
- BGE Reranker를 사용한 결과 재정렬
- Gemini AI를 활용한 자연어 답변 생성
- 반응형 웹 디자인