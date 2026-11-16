import os
import requests
import streamlit as st


# =====================================================
# 1. APPLICATION CONFIGURATION
# =====================================================

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="Enterprise AI Knowledge Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =====================================================
# 2. SESSION STATE
# =====================================================

if "document_id" not in st.session_state:
    st.session_state.document_id = None

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =====================================================
# 3. API REQUEST HELPER
# =====================================================

def api_request(method, endpoint, **kwargs):

    url = f"{API_BASE_URL}{endpoint}"

    try:

        response = requests.request(
            method=method,
            url=url,
            timeout=180,
            **kwargs
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "Cannot connect to the backend. "
            "Please start FastAPI."
        )

    except requests.exceptions.Timeout:

        st.error(
            "The request took too long. Please try again."
        )

    except requests.exceptions.HTTPError:

        try:
            error_message = response.json().get(
                "detail",
                response.text
            )
        except ValueError:
            error_message = response.text

        st.error(f"Backend error: {error_message}")

    except requests.exceptions.RequestException as error:

        st.error(f"Request failed: {error}")

    return None


# =====================================================
# 4. APPLICATION HEADER
# =====================================================

st.title("🤖 Enterprise AI Knowledge Assistant")

st.markdown(
    """
    Upload your PDF and start a conversation with your document.
    Get intelligent answers powered by Retrieval-Augmented Generation.
    """
)

st.divider()


# =====================================================
# 5. PDF UPLOAD SECTION
# =====================================================

if st.session_state.document_id is None:

    st.markdown("### 📄 Upload Your PDF")

    uploaded_file = st.file_uploader(
        "Select one PDF document",
        type=["pdf"],
        accept_multiple_files=False,
        help="Upload one PDF to start your AI conversation."
    )

    if uploaded_file is not None:

        st.info(
            f"Selected file: **{uploaded_file.name}**"
        )

        if st.button(
            "Upload and Start Chat",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Preparing your document for AI chat..."
            ):

                # One API call performs the complete
                # upload and indexing pipeline.

                result = api_request(
                    method="POST",
                    endpoint="/documents/upload-and-index",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }
                )

            if result is not None:

                document_id = result.get("document_id")

                if not document_id:

                    st.error(
                        "Backend did not return a document ID."
                    )

                else:

                    # Save document information
                    st.session_state.document_id = document_id

                    st.session_state.document_name = (
                        result.get("filename", uploaded_file.name)
                    )

                    # Start a fresh conversation
                    st.session_state.chat_history = []

                    st.success(
                        "Your document is ready! You can start chatting."
                    )

                    # Hide uploader and display chat
                    st.rerun()


# =====================================================
# 6. CHAT SECTION
# =====================================================

else:

    st.markdown("### 💬 Chat With Your Document")

    st.caption(
        f"📄 Connected document: {st.session_state.document_name}"
    )

    st.divider()

    # -------------------------------------------------
    # 6.1 Display welcome message
    # -------------------------------------------------

    if not st.session_state.chat_history:

        with st.chat_message("assistant"):

            st.markdown(
                """
                Hello! 👋

                Your document has been successfully processed.

                You can now ask questions about its content.
                """
            )

    # -------------------------------------------------
    # 6.2 Display previous conversation
    # -------------------------------------------------

    for message in st.session_state.chat_history:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            sources = message.get("sources", [])

            if sources:

                with st.expander("📚 View Sources"):

                    for index, source in enumerate(
                        sources,
                        start=1
                    ):

                        st.markdown(
                            f"**Source {index}**"
                        )

                        st.write(
                            f"Page number: {source.get('page_number', 'N/A')}"
                        )

                        if source.get("score") is not None:

                            st.caption(
                                f"Relevance score: {source['score']:.4f}"
                            )

    # -------------------------------------------------
    # 6.3 Chat input
    # -------------------------------------------------

    user_question = st.chat_input(
        "Ask anything about your uploaded PDF..."
    )

    if user_question:

        # Display user message
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):

            st.markdown(user_question)

        # -------------------------------------------------
        # 6.4 Call FastAPI chat endpoint
        # -------------------------------------------------

        with st.chat_message("assistant"):

            with st.spinner(
                "Searching your document and generating an answer..."
            ):

                result = api_request(
                    method="POST",
                    endpoint="/chat/query",
                    json={
                        "document_id": st.session_state.document_id,
                        "question": user_question
                    }
                )

            if result is not None:

                answer = result.get(
                    "answer",
                    "No answer was generated."
                )

                sources = result.get("sources", [])

                st.markdown(answer)

                # Display source references
                if sources:

                    with st.expander("📚 View Sources"):

                        for index, source in enumerate(
                            sources,
                            start=1
                        ):

                            st.markdown(
                                f"**Source {index}**"
                            )

                            st.write(
                                f"Page: {source.get('page_number', 'N/A')}"
                            )

                            if source.get("score") is not None:

                                st.caption(
                                    f"Relevance: {source['score']:.4f}"
                                )

                # Save assistant response
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": sources
                })

            else:

                st.warning(
                    "Unable to generate an answer. "
                    "Please try again."
                )

                # Remove unanswered user message
                st.session_state.chat_history.pop()