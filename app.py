
import streamlit as st
from io import BytesIO

from pdf_extractor import extract_pdf_text
from text_chunker import split_text_into_chunks
from embedding_service import create_embeddings, search_similar_chunks
from ai_service import generate_answer


st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Assistant")
st.write("Upload multiple PDFs and ask questions about their content.")


# Initialize session state
if "documents" not in st.session_state:
    st.session_state.documents = {}


# Multiple PDF upload
uploaded_files = st.file_uploader(
    "Upload your PDF documents",
    type=["pdf"],
    accept_multiple_files=True
)


# Process uploaded PDFs
if uploaded_files and st.button("Process Documents"):

    try:
        for uploaded_file in uploaded_files:

            file_name = uploaded_file.name

            if file_name in st.session_state.documents:
                st.info(f"{file_name} is already processed.")
                continue

            with st.spinner(f"Processing {file_name}..."):

                pages = extract_pdf_text(
                    BytesIO(uploaded_file.getvalue())
                )

                if not pages:
                    st.warning(f"No readable text found in {file_name}.")
                    continue

                chunks = split_text_into_chunks(pages)
                embeddings = create_embeddings(chunks)

                st.session_state.documents[file_name] = {
                    "chunks": chunks,
                    "embeddings": embeddings,
                    "messages": []
                }

                st.success(
                    f"{file_name} processed successfully! "
                    f"{len(chunks)} chunks created."
                )

    except Exception as error:
        st.error(f"Error processing documents: {error}")


# Display processed documents
if st.session_state.documents:

    st.divider()
    st.subheader("📚 Your Documents")

    for file_name in st.session_state.documents:
        st.write(f"📄 {file_name}")

    st.divider()

    # Select a document
    selected_document = st.selectbox(
        "Choose a document to chat with",
        list(st.session_state.documents.keys())
    )

    # Get selected document
    document = st.session_state.documents[selected_document]

    # Initialize chat history for older processed documents
    if "messages" not in document:
        document["messages"] = []

    # Delete selected document
    if st.button("🗑️ Delete Selected Document"):

        del st.session_state.documents[selected_document]

        st.success(f"{selected_document} deleted successfully!")

        st.rerun()

    st.divider()

    st.subheader(f"💬 Chat with {selected_document}")

    # Display selected document's chat history
    for message in document["messages"]:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Ask question
    question = st.chat_input(
        "Ask a question about this document..."
    )

    if question:

        # Save user message
        document["messages"].append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching document and generating answer..."
            ):

                try:

                    results = search_similar_chunks(
                        question,
                        document["chunks"],
                        document["embeddings"],
                        top_k=5,
                        program_filter=None
                    )

                    answer = generate_answer(question, results)

                    st.markdown(answer)

                    # Save assistant response
                    document["messages"].append({
                        "role": "assistant",
                        "content": answer
                    })

                except Exception as error:
                    st.error(f"Error generating answer: {error}")

else:
    st.info("Upload one or more PDFs and click Process Documents.")
