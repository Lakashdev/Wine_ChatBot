import sys
import os

# Ensure parent directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from openai import OpenAI
from retriever.retriever import WineRetriever

# Initialize DeepSeek-compatible client
client = OpenAI(
    api_key="sk-efc9807bf70b4426a1ec62e790cb9697",
    base_url="https://api.deepseek.com"
)

# Initialize retriever
retriever = WineRetriever(
    index_path="data/processed/wine_embeddings.index",
    docs_path="data/processed/wine_docs.pkl"
)

def answer_query_rag(user_query, followup_context=None):
    """
    Retrieve context using FAISS unless followup_context is provided.
    Then, build a prompt and get LLM response.
    Returns both the answer and associated wine sources (title, permalink, image).
    """
    # Use provided context if follow-up
    context_docs = followup_context if followup_context else retriever.query(user_query)

    if not context_docs:
        return "Sorry, I couldn't find any matching wines at the moment."

    wine_descriptions = []
    sources = []

    for doc in context_docs:
        if isinstance(doc, dict):
            wine_descriptions.append(doc.get("document", ""))
            sources.append({
                "title": doc.get("Title", "Unknown Wine"),
                "permalink": doc.get("Permalink", ""),
                "image": doc.get("Image_URL", doc.get("Image", ""))
            })
        else:
            wine_descriptions.append(doc)

    context = "\n\n".join(wine_descriptions)

    prompt = f"""You are a wine sommelier assistant. Use the following wine descriptions to answer clearly and helpfully.

Context:
{context}

User question: {user_query}
Answer:"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": sources
    }
