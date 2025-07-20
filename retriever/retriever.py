import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

class WineRetriever:
    def __init__(self, index_path, docs_path):
        self.index = faiss.read_index(index_path)
        with open(docs_path, "rb") as f:
            self.docs = pickle.load(f)
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def query(self, text, k=5):
        emb = self.model.encode([text])
        emb = np.array(emb).astype("float32")
        D, I = self.index.search(emb, k)
        return [self.docs[i] for i in I[0]]
