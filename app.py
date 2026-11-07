
import streamlit as st
from io import BytesIO

from pdf_extractor import extract_pdf_text
from text_chunker import split_text_into_chunks
from embedding_service import create_embeddings, search_similar_chunks
from ai_service import generate_answer

st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄"
)

st.title("📄 AI Document Assistant")
st.write("Upload a PDF and ask questions about it.")

uploaded_file = st.file_uploader("Upload your PDF", type=["pdf"])

if uploaded_file and st.button("Process PDF"):

    with st.spinner("Processing PDF..."):
        pages = extract_pdf_text(BytesIO(uploaded_file.getvalue()))

        if pages:
            chunks = split_text_into_chunks(pages)
            embeddings = create_embeddings(chunks)

            st.session_state.chunks = chunks
            st.session_state.embeddings = embeddings
            st.session_state.messages = []

            st.success(f"PDF processed! {len(chunks)} chunks created.")
        else:
            st.error("No readable text found.")

if "chunks" in st.session_state:

    st.subheader("Ask questions about your PDF")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask something about your PDF...")

    if question:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Finding the answer..."):

                results = search_similar_chunks(
                    question,
                    st.session_state.chunks,
                    st.session_state.embeddings,
                    top_k=5,
                )

                answer = generate_answer(question, results)

                st.markdown(answer)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })
