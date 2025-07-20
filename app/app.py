
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from generator.generator import answer_query_rag


while True:
    user_input = input("You: ")
    if user_input.lower() == "exit":
        break
    answer = answer_query_rag(user_input)
    print("Bot:", answer)