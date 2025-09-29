import streamlit as st
import sys
import os

# Ensure access to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator.generator import answer_query_rag

# Streamlit setup
st.set_page_config(page_title="🍷 Wine Sommelier Chatbot", layout="centered")
st.title("🍇 Wine Chatbot")
st.markdown("Ask me anything about wine, pairing, region, or recommendations!")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# User input
user_query = st.chat_input("Type your wine question here...")

def render_wine_card_md(wine):
    """Render a wine card using Markdown so it shows properly in chat."""
    title = wine.get("title", "Unnamed Wine")
    region = wine.get("region", "N/A")
    price = wine.get("price", "N/A")
    aromas = wine.get("aromas", "N/A")
    pairing = wine.get("pairing", "N/A")
    wine_type = wine.get("type", "N/A")
    alcohol = wine.get("alcohol", "N/A")
    why = wine.get("why", "N/A")
    link = wine.get("permalink", "")
    image = wine.get("image", "")

    parts = []

    if image:
        parts.append(f"![]({image})")

    parts.append(f"### 🍷 {title}")
    parts.append(f"- **Region:** {region}")
    parts.append(f"- **Type:** {wine_type}")
    parts.append(f"- **Aromas/Flavors:** {aromas}")
    parts.append(f"- **Pairings:** {pairing}")
    parts.append(f"- **Alcohol:** {alcohol}")
    parts.append(f"- **Price:** {price}")
    parts.append(f"- **Why Try It?** {why}")

    if link:
        parts.append(f"- [🔗 Buy Here]({link})")

    card_md = "\n".join(parts)
    st.markdown(card_md, unsafe_allow_html=True)

# Process user query
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = answer_query_rag(user_query)

                if isinstance(response, dict) and "answer" in response:
                    answer_text = response["answer"]
                    wines = response.get("structured_wines", [])
                    st.session_state.last_sources = wines

                    if wines:
                        for wine in wines:
                            render_wine_card_md(wine)

                    if answer_text:
                        st.markdown(f"**Suggested Choice Based on Preference:**\n\n{answer_text}", unsafe_allow_html=True)

                    st.session_state.messages.append({"role": "assistant", "content": answer_text})
                else:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"Error: {e}")
