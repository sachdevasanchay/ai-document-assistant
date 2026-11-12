
import streamlit as st
from io import BytesIO

from pdf_extractor import extract_pdf_text
from text_chunker import split_text_into_chunks
from embedding_service import create_embeddings, search_similar_chunks
from ai_service import generate_answer

from db_service import (
    save_document,
    get_documents,
    get_conversations,
    save_conversation,
    delete_document,
    rename_conversation,
    delete_conversation
)


st.set_page_config(
    page_title="AI Document Assistant",
    page_icon="📄",
    layout="wide"
)

st.title("📄 AI Document Assistant")
st.write("Upload multiple PDFs and ask questions about their content.")


# Initialize session state and load documents from MongoDB
if "documents" not in st.session_state:

    st.session_state.documents = {}

    try:

        saved_documents = get_documents()

        for saved_document in saved_documents:

            file_name = saved_document["file_name"]
            chunks = saved_document.get("chunks", [])

            if not chunks:
                continue

            # Recreate embeddings from saved chunks
            embeddings = create_embeddings(chunks)

            # Load conversations from MongoDB
            conversations = get_conversations(file_name)

            if not conversations:

                conversations = {
                    "Conversation 1": {
                        "messages": []
                    }
                }

                save_conversation(
                    file_name,
                    "Conversation 1",
                    []
                )

            st.session_state.documents[file_name] = {
                "chunks": chunks,
                "embeddings": embeddings,
                "conversations": conversations,
                "active_conversation": list(conversations.keys())[0]
            }

    except Exception as error:

        st.error(f"Error loading documents from MongoDB: {error}")


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

                    st.warning(
                        f"No readable text found in {file_name}."
                    )

                    continue

                chunks = split_text_into_chunks(pages)

                embeddings = create_embeddings(chunks)

                # Save extracted document data in MongoDB
                save_document(file_name, chunks)

                # Create initial conversation
                conversations = {
                    "Conversation 1": {
                        "messages": []
                    }
                }

                save_conversation(
                    file_name,
                    "Conversation 1",
                    []
                )

                st.session_state.documents[file_name] = {
                    "chunks": chunks,
                    "embeddings": embeddings,
                    "conversations": conversations,
                    "active_conversation": "Conversation 1"
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

    # Select document
    selected_document = st.selectbox(
        "Choose a document to chat with",
        list(st.session_state.documents.keys())
    )

    document = st.session_state.documents[selected_document]

    # Migrate older session-state documents if necessary
    if "conversations" not in document:

        old_messages = document.pop("messages", [])

        document["conversations"] = {
            "Conversation 1": {
                "messages": old_messages
            }
        }

        document["active_conversation"] = "Conversation 1"

        save_conversation(
            selected_document,
            "Conversation 1",
            old_messages
        )

    # Delete selected document
    if st.button("🗑️ Delete Selected Document"):

        try:

            delete_document(selected_document)

            del st.session_state.documents[selected_document]

            st.success(
                f"{selected_document} deleted successfully!"
            )

            st.rerun()

        except Exception as error:

            st.error(f"Error deleting document: {error}")

    st.divider()

    # Conversation management
    st.subheader("💬 Conversation Management")

    conversations = document["conversations"]

    # Create new conversation
    if st.button("➕ New Conversation"):

        conversation_number = 1

        while f"Conversation {conversation_number}" in conversations:

            conversation_number += 1

        new_conversation = f"Conversation {conversation_number}"

        conversations[new_conversation] = {
            "messages": []
        }

        document["active_conversation"] = new_conversation

        # Save new conversation in MongoDB
        save_conversation(
            selected_document,
            new_conversation,
            []
        )

        st.rerun()

    # Select conversation
    conversation_names = list(conversations.keys())

    active_conversation = document["active_conversation"]

    selected_conversation = st.selectbox(
        "Select a conversation",
        conversation_names,
        index=conversation_names.index(active_conversation)
    )

    document["active_conversation"] = selected_conversation

    conversation = conversations[selected_conversation]

    # Rename and delete conversation
    col1, col2 = st.columns(2)

    with col1:

        new_name = st.text_input(
            "Rename conversation",
            value=selected_conversation,
            key=f"rename_{selected_document}_{selected_conversation}"
        )

        if st.button(
            "✏️ Rename",
            key=f"rename_button_{selected_document}_{selected_conversation}"
        ):

            new_name = new_name.strip()

            if not new_name:

                st.warning("Conversation name cannot be empty.")

            elif new_name in conversations:

                st.warning(
                    "A conversation with this name already exists."
                )

            else:

                try:

                    result = rename_conversation(
                        selected_document,
                        selected_conversation,
                        new_name
                    )

                    if result.matched_count:

                        conversations[new_name] = conversations.pop(
                            selected_conversation
                        )

                        document["active_conversation"] = new_name

                        st.success(
                            "Conversation renamed successfully!"
                        )

                        st.rerun()

                    else:

                        st.error("Conversation not found in MongoDB.")

                except Exception as error:

                    st.error(
                        f"Error renaming conversation: {error}"
                    )

    with col2:

        if st.button(
            "🗑️ Delete Conversation",
            key=f"delete_conversation_{selected_document}_{selected_conversation}"
        ):

            try:

                delete_conversation(
                    selected_document,
                    selected_conversation
                )

                if len(conversations) > 1:

                    del conversations[selected_conversation]

                    document["active_conversation"] = list(
                        conversations.keys()
                    )[0]

                else:

                    conversations[selected_conversation]["messages"] = []

                    # Save the empty conversation again
                    save_conversation(
                        selected_document,
                        selected_conversation,
                        []
                    )

                st.success("Conversation deleted successfully!")

                st.rerun()

            except Exception as error:

                st.error(
                    f"Error deleting conversation: {error}"
                )

    st.divider()

    # Chat section
    st.subheader(f"💬 Chat: {selected_conversation}")

    messages = conversation["messages"]

    # Display chat history
    for message in messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            # Display saved source information
            if message.get("sources"):

                with st.expander("📚 View source information"):

                    for source in message["sources"]:

                        st.markdown(
                            f"**Page {source['page']}**"
                        )

                        st.write(source["text"])

                        st.divider()

    # Ask question
    question = st.chat_input(
        "Ask a question about this document..."
    )

    if question:

        # Save user message
        messages.append({
            "role": "user",
            "content": question
        })

        # Immediately save user message in MongoDB
        save_conversation(
            selected_document,
            selected_conversation,
            messages
        )

        with st.chat_message("user"):

            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching document and generating answer..."
            ):

                try:

                    # Search relevant chunks
                    results = search_similar_chunks(
                        question,
                        document["chunks"],
                        document["embeddings"],
                        top_k=5,
                        program_filter=None
                    )

                    # Generate AI answer
                    answer = generate_answer(
                        question,
                        results
                    )

                    st.markdown(answer)

                    # Display source information
                    if results:

                        with st.expander(
                            "📚 View source information"
                        ):

                            for source in results:

                                st.markdown(
                                    f"**Page {source['page']}**"
                                )

                                st.write(source["text"])

                                st.divider()

                    # Save assistant response and sources
                    messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": results
                    })

                    # Save complete conversation in MongoDB
                    save_conversation(
                        selected_document,
                        selected_conversation,
                        messages
                    )

                except Exception as error:

                    st.error(
                        f"Error generating answer: {error}"
                    )

else:

    st.info(
        "Upload one or more PDFs and click Process Documents."
    )
