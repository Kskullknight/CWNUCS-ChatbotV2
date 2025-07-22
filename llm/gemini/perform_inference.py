from .init_llm import init_QA_gemini

chain = init_QA_gemini()

def llmResponse(question:str , docs:str):

    result = chain.invoke({
        "userQuery" : question,
        "docs" : docs}
    )

    return result


