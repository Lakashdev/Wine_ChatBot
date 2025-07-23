import streamlit as st
import sys
import os

# Ensure access to project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generator.generator import answer_query_rag

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

# Input from user
user_query = st.chat_input("Type your wine question here...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Follow-up intent like "where can I buy it"
                if any(kw in user_query.lower() for kw in ["buy it", "purchase it", "where to get it", "where can i buy"]):
                    if st.session_state.last_sources:
                        response = "Here are the wines you asked about earlier:\n\n"
                        for wine in st.session_state.last_sources:
                            title = wine.get("title", "Wine")
                            link = wine.get("permalink", "")
                            img = wine.get("image", "")

                            if img:
                                st.image(img, caption=title, use_column_width=True)
                            st.markdown(f"🔗 [{title}]({link})", unsafe_allow_html=True)

                            response += f"- [{title}]({link})\n"
                    else:
                        response = "Sorry, I don’t have a previous wine to reference. Could you ask again with wine details?"

                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

                else:
                    # Main RAG response
                    response = answer_query_rag(user_query)

                    if isinstance(response, dict) and "answer" in response:
                        answer_text = response["answer"]
                        sources = response.get("sources", [])
                        shown_titles = set()

                        # Show any wine image mentioned in the answer
                        for wine in sources:
                            title = wine.get("title", "").strip()
                            image_url = wine.get("image", "")
                            if title and image_url and title.lower() in answer_text.lower() and title not in shown_titles:
                                st.markdown(f"**{title}**", unsafe_allow_html=True)
                                st.image(image_url, caption=title, use_column_width=True)
                                shown_titles.add(title)

                        st.markdown(answer_text, unsafe_allow_html=True)

                        # Show all sources with small image preview and link
                        if sources:
                            for wine in sources:
                                title = wine.get("title", "Unknown Wine")
                                link = wine.get("permalink", "")
                                img = wine.get("image", "")

                                cols = st.columns([1, 5])
                                with cols[0]:
                                    if img:
                                        st.image(img, width=60)
                                with cols[1]:
                                    st.markdown(f"🔗 [{title}]({link})", unsafe_allow_html=True)

                            st.session_state.last_sources = sources

                        full_response = answer_text + "\n\n" + "\n".join(
                            [f"[{w['title']}]({w['permalink']})" for w in sources]
                        )
                        st.session_state.messages.append({"role": "assistant", "content": full_response})
                    else:
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})

            except Exception as e:
                st.error(f"Error: {e}")
