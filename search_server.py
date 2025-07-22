import sys, os
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(PROJECT_ROOT)

from retriever.retriever import make_retriever, parse_search_results, embeddings
from reranker.reranking import reranking

from llm.gemini.perform_inference import llmResponse

# 전역 변수로 Retriever 선언
denseRetriever = None
sparseRetriever = None

def initialize_retrievers():
    global denseRetriever, sparseRetriever

    print("검색 시스템을 초기화하는 중입니다...")
    denseRetriever, sparseRetriever = make_retriever()
    print("검색 시스템 초기화 완료!\n")


def search_and_rerank(query, top_k=10):
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


def main():
    # 시작 시 Retriever 초기화
    initialize_retrievers()
    
    print("=== 창원대학교 검색 시스템 ===")
    print("종료하려면 'quit' 또는 'exit'를 입력하세요.\n")
    
    while True:
        # 사용자 입력 받기
        query = input("\n검색할 내용을 입력하세요: ").strip()
        
        # 종료 조건
        if query.lower() in ['quit', 'exit', '종료']:
            print("검색 시스템을 종료합니다.")
            break
        
        if not query:
            print("검색어를 입력해주세요.")
            continue
        
        print(f"\n'{query}'에 대한 검색을 수행합니다...")
        
        try:
            # 검색 및 리랭킹 수행
            results = search_and_rerank(query, top_k=5)
            
            # 결과 출력
            print(f"\n검색 결과 (상위 {len(results)}개):")
            print("=" * 80)
            
            for i, result in enumerate(results):
                content, score, metadata = result
                print(f"\n[{i+1}] 점수: {score:.4f}")
                print(f"제목: {metadata.get('number', 'N/A')} - {metadata.get('author', '작성자 없음')}")
                print(f"날짜: {metadata.get('date', '날짜 없음')} | 조회수: {metadata.get('views', '0')}")
                print(f"URL: {metadata.get('url', 'URL 없음')}")
                print(f"내용 미리보기: {content[:200]}...")
                print("-" * 80)
        
            llm_response = llmResponse(query, results)

            print("LLM 최종답변 -> ")
            print(llm_response)
        except Exception as e:
            print(f"검색 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()