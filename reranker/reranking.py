from FlagEmbedding import FlagReranker
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True, devices='cuda:3')

# [question, title, id]
def reranking(titles: list[str]) -> list[str]:

    # compute_score 함수는 [0], [1] 만 사용하고 뒤에 메타데이터는 그대로 리턴함
    scores = reranker.compute_score(titles, normalize=True)
    """title = [질문, 검색결과, 메타데이터]"""

    results = [[title[1], score, title[2]] for title, score in zip(titles, scores)]
    results = sorted(results, key=lambda x:x[1], reverse=True)
    
    # 희소검색과 밀집검색에서 둘다 매칭이 된 경우의 중복을 제거하는 코드임
    seen_numbers = set()
    unique_results = []
    
    for result in results:
        number = result[2].get('number')
        if number and number not in seen_numbers:
            seen_numbers.add(number)
            unique_results.append(result)
    
    return unique_results

