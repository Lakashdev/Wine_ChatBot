import pandas as pd
import numpy as np
import pickle
import faiss
import os
from sentence_transformers import SentenceTransformer

# === Setup paths ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_PATH = os.path.join(BASE_DIR, "..", "data", "processed", "wine_docs.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
INDEX_PATH = os.path.join(OUTPUT_DIR, "wine_embeddings.index")
DOCS_PKL_PATH = os.path.join(OUTPUT_DIR, "wine_docs.pkl")

# Ensure output folder exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Load wine documents ===
print(f"📂 Loading wine data from: {DOC_PATH}")
df = pd.read_csv(DOC_PATH)
docs = df['document'].dropna().tolist()
print(f"📄 Loaded {len(docs)} wine documents")

# === Parse document string into structured metadata ===
def parse_document(doc):
    fields = {
        "Title": None,
        "Aromas": None,
        "Flavors": None,
        "Food_Pairings": None,
        "Type": None,
        "Alcohol": None,
        "Price": None,
        "Region": None,
        "Fullness": None,
        "Astringency": None,
        "Acidity": None,
        "Why_Try": None,
        "Image_URL": None,
        "Permalink": None,
        "document": doc  # keep full original
    }

    try:
        lines = doc.strip().split(".\n")
        for line in lines:
            line = line.strip().replace("amp;", "")  # Clean HTML noise
            if line.lower().startswith("wine:"):
                fields["Title"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("aromas:"):
                fields["Aromas"] = line.split(":", 1)[1].strip().replace("|", ", ")
            elif line.lower().startswith("flavors:"):
                fields["Flavors"] = line.split(":", 1)[1].strip().replace("|", ", ")
            elif line.lower().startswith("food pairings:"):
                fields["Food_Pairings"] = line.split(":", 1)[1].strip().replace("|", ", ")
            elif line.lower().startswith("type:"):
                fields["Type"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("alcohol:"):
                fields["Alcohol"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("price:"):
                fields["Price"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("region:"):
                fields["Region"] = line.split(":", 1)[1].strip().replace("|", ", ")
            elif line.lower().startswith("fullness/sweetness:"):
                fields["Fullness"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("astringency:"):
                fields["Astringency"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("acidity:"):
                fields["Acidity"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("buy here:"):
                fields["Permalink"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("image url:"):
                fields["Image_URL"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("description:"):
                fields["Why_Try"] = line.split(":", 1)[1].strip()
    except Exception as e:
        print(f"⚠️ Error parsing doc: {e}")
    
    return fields

structured_docs = [parse_document(doc) for doc in docs]

# === Generate embeddings ===
print("🧠 Generating embeddings with MiniLM...")
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(docs, show_progress_bar=True)
embeddings = np.array(embeddings).astype("float32")

# === Build and save FAISS index ===
print("💾 Saving FAISS index and structured doc list...")
index = faiss.IndexFlatL2(384)
index.add(embeddings)

faiss.write_index(index, INDEX_PATH)
with open(DOCS_PKL_PATH, "wb") as f:
    pickle.dump(structured_docs, f)

print("✅ Embedding and indexing complete.")
print(f"→ Saved index: {INDEX_PATH}")
print(f"→ Saved structured docs: {DOCS_PKL_PATH}")
