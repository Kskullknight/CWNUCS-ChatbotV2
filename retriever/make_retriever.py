from dotenv import load_dotenv
load_dotenv()

from read_json_data import JsonDataLoader

import glob, mysql.connector, faiss, pickle
from langchain_community.vectorstores import FAISS
from langchain_teddynote.retrievers import KiwiBM25Retriever

from langchain_upstage import UpstageEmbeddings
# embeddings = UpstageEmbeddings(model="solar-embedding-1-large")
# query_embeddings = UpstageEmbeddings(model="solar-embedding-1-large-query")
upstage_embedding = UpstageEmbeddings(model="solar-embedding-1-large")

def get_embed(titles):
    embeddings = []; original_titles = []; all_meta_data = []
    batch_size = 100
    for idx in range(0,len(titles),batch_size):
        print("processing...",idx, len(titles))

        start = idx
        end = min(idx + batch_size,len(titles))

        title_and_abstract = [d[0][:8000] for d in titles[start:end]]
        meta_data = [d[1] for d in titles[start:end]]
        
        try:
            embedding = upstage_embedding.embed_documents((title_and_abstract))
        except Exception as e:
            print("Token Length Error, cut 5000 length")
            title_and_abstract = [d[0][:5000] for d in titles[start:end]]
            embedding = upstage_embedding.embed_documents((title_and_abstract))
        
        original_titles.extend(title_and_abstract)
        embeddings.extend(embedding)
        all_meta_data.extend(meta_data)
   
    return original_titles, embeddings, all_meta_data



