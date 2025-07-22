
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI  
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()

#from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field
import os
import requests
import json
import re
from datetime import datetime

def load_prompt_from_file(function_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))

    project_root = os.path.dirname(os.path.dirname(current_dir))
    prompt_path = os.path.join(project_root, 'llm', 'prompts', f'{function_name}.txt')
    
    with open(prompt_path, 'r', encoding='utf-8') as file:
        return file.read()

def init_QA_gemini():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.56,
        max_output_tokens=8192 * 5,
        thinking_budget=2048,
        disable_streaming=False,
    )
    
    prompt_text = load_prompt_from_file('init_QA_gemini')
    prompt = PromptTemplate.from_template(prompt_text)
    chain = prompt | llm | StrOutputParser()

    return chain

# chain = init_QA_gemini()

# result = chain.invoke({"userQuery" : "이 공지사항은 무슨 내용인가요?", "docs" : "2025년도 2학기 수강신청 안내... 수강신청은 자동으로 이루어지므로 개별적으로 신청하지 않아도.."})
# print(result)
