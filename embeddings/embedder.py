import pandas as pd
import numpy as np
import pickle
import faiss
import os
from sentence_transformers import SentenceTransformer

# Resolve absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "wine_docs.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
INDEX_PATH = os.path.join(OUTPUT_DIR, "wine_embeddings.index")
DOCS_PKL_PATH = os.path.join(OUTPUT_DIR, "wine_docs.pkl")

# Ensure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load preprocessed docs
print(f"Loading documents from: {DOC_PATH}")
data = pd.read_csv(DOC_PATH)
docs = data['document'].dropna().tolist()

print(f"Loaded {len(docs)} wine documents")

# Generate embeddings
print("Generating embeddings with MiniLM...")
model = SentenceTransformer('all-MiniLM-L6-v2')
embeddings = model.encode(docs, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# Build and save FAISS index
print("Saving FAISS index and document list...")
index = faiss.IndexFlatL2(384)
index.add(embeddings)

faiss.write_index(index, INDEX_PATH)
with open(DOCS_PKL_PATH, "wb") as f:
    pickle.dump(docs, f)

print("✅ Embedding and indexing complete.")
print(f"→ Saved index: {INDEX_PATH}")
print(f"→ Saved docs:  {DOCS_PKL_PATH}")
