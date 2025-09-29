# test_docs.py
import pickle

with open("E:\VC_data\Chatbot\data\processed\wine_docs.pkl", "rb") as f:
    docs = pickle.load(f)

print("🔍 Type of first doc:", type(docs[0]))
print("🗝️ Keys in first doc:", docs[0].keys())