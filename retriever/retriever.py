import os
import numpy as np
import pickle
import faiss
from sentence_transformers import SentenceTransformer

class WineRetriever:
    def __init__(self, index_path: str, docs_path: str):
        # 1) Load model and index
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(index_path)

        # 2) Sanity checks
        faiss_dim = self.index.d
        model_dim = getattr(self.model, "get_sentence_embedding_dimension", lambda: None)()
        if model_dim is None:
            # Fallback: compute once
            test_vec = self.model.encode(["test"])
            model_dim = int(test_vec.shape[1])

        if faiss_dim != model_dim:
            raise ValueError(
                f"FAISS dim ({faiss_dim}) != model dim ({model_dim}). "
                "Rebuild the index with the same model as the retriever."
            )

        # 3) Load structured docs (list of dicts)
        with open(docs_path, "rb") as f:
            self.documents = pickle.load(f)

        if not isinstance(self.documents, list) or not self.documents:
            raise ValueError("Loaded documents are empty or not a list.")

        if not isinstance(self.documents[0], dict):
            raise ValueError(
                "Documents are not structured dicts. "
                "Rebuild wine_docs.pkl using the updated embedder that parses fields."
            )

        # Optional: warn if index/docs counts are very different
        if self.index.ntotal and abs(self.index.ntotal - len(self.documents)) > 0:
            # Not necessarily an error, but helpful to know
            print(
                f"⚠️ Index vectors: {self.index.ntotal}, docs: {len(self.documents)}. "
                "They should generally match."
            )

        print(
            f"✅ Retriever ready | index dim={faiss_dim}, items={self.index.ntotal}, "
            f"docs={len(self.documents)}"
        )

    @staticmethod
    def _normalize(text: str) -> str:
        return (text or "").strip()

    def embed(self, text: str) -> np.ndarray:
        text = self._normalize(text)
        vec = self.model.encode([text])  # (1, dim)
        return np.asarray(vec, dtype="float32")

    def query(self, user_query: str, k: int = 5):
        if self.index.ntotal == 0:
            return []

        k = max(1, min(k, self.index.ntotal))  # clamp
        qv = self.embed(user_query)
        distances, indices = self.index.search(qv, k)

        # Collect structured dicts
        results = []
        for idx in indices[0]:
            if 0 <= idx < len(self.documents):
                results.append(self.documents[idx])

        # Debug prints to confirm structure
        if results:
            sample = results[0]
            print("🔎 query() sample keys:", list(sample.keys())[:10])
        else:
            print("🔎 query() returned no results")

        return results
