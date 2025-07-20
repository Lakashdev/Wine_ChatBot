import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import OpenAI
from retriever.retriever import WineRetriever

client = OpenAI(api_key="sk-efc9807bf70b4426a1ec62e790cb9697", base_url="https://api.deepseek.com")
retriever = WineRetriever(
    index_path="../data/processed/wine_embeddings.index",
    docs_path="../data/processed/wine_docs.pkl"
)

def answer_query_rag(user_query):
    context_docs = retriever.query(user_query)
    context = "\n".join(context_docs)

    prompt = f"""You are a wine sommelier assistant. Use the following wine descriptions to answer clearly and helpfully.

Context:
{context}

User question: {user_query}
Answer:"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content