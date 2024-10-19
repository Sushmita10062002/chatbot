import streamlit as st
import requests
from openai import OpenAI
import base64
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env")

PDF_PROCESSING_API = os.environ.get("PDF_PROCESSING_API")
GET_RELEVANT_DOCS = os.environ.get("GET_RELEVANT_DOCS")
GET_RERANKED_DOCS = os.environ.get("GET_RERANKED_DOCS")

system_prompt = '''
You are Samantha.ai. Your primary role is to assist the user by answering the question from the context given to you.
You are provided with the context, which contains extracts from various information sources, which may or may not be relevant to the user query.
If you do not have enough context to answer the query, politely inform the user that "Hmm, I don't know enough to give you a confident answer yet."

<Context>
{context}
'''

# Initialize session state variables
if "pdf_id" not in st.session_state:
    st.session_state.pdf_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Function to get OpenAI chat completion
def chat_completion_request(messages, stream = True):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0,
        max_tokens=500,
        stream=stream,
    )
    return response

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

st.set_page_config(page_title="PDF Chatbot", layout="wide")
st.title("PDF Chatbot")

with st.sidebar:
    st.header("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None and st.session_state.pdf_id is None:
        st.write("Processing the uploaded PDF...")
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
        try:
            response = requests.post(PDF_PROCESSING_API, files=files)
            if response.status_code == 200:
                st.session_state.pdf_id = response.json().get("pdf_id")
                st.success(f"PDF processed successfully.")
            else:
                st.error("Failed to process the PDF.")
        except Exception as e:
            st.error(f"An error occurred: {e}. Please try again later!")

if st.session_state.pdf_id:
    st.write("You can now ask questions related to the processed PDF.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"], avatar=message.get("avatar")):
            st.markdown(message["content"])
            if message["role"] == "assistant" and "citations" in message:
                with st.expander("View Citations"):
                    for idx, citation in enumerate(message["citations"], 1):
                        st.markdown(f'''
                                    <span style="color:cyan; font-weight:bold;">Citation {idx}:</span> 
                                    {citation['text']}
                                    (<a href="#" style="color:orange;">Page: {citation['page_num']}</a>)
                                ''', unsafe_allow_html=True)

    user_question = st.chat_input("Ask Samantha a question:")

    if user_question:
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_question,
            "avatar": "👤"
        })

        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_question)

        # Get bot response
        payload = {
            "pdf_id": st.session_state.pdf_id,
            "question": user_question
        }
        try:
            response = requests.post(GET_RELEVANT_DOCS, json=payload)
            if response.status_code == 200:        
                retrieved_docs = response.json().get("retrieved_docs")
                reranked_docs = requests.post(GET_RERANKED_DOCS, json = {"question": user_question, "docs": [doc["text"] for doc in retrieved_docs]}).json().get("reranked_docs")
                context = "\n\n".join([retrieved_docs[doc["index"]]["text"] for doc in reranked_docs])

                messages = [{"role": "system", "content": system_prompt.format(context=context)}, {"role": "user", "content": user_question}]
                response = chat_completion_request(messages)

                response_tokens = ""
                with st.chat_message("assistant", avatar="🤖"):
                    container = st.empty()

                    for chunk in response:
                        # Generate response
                        try:
                            token = chunk.choices[0].delta.content
                        except:
                            token = chunk
                            if (token != None):
                                token += " "
                        
                        if isinstance(token, str):
                            response_tokens += token

                        container.write(response_tokens)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_tokens,
                    "avatar": "🤖",
                    "citations": [{"text": retrieved_docs[doc["index"]]["text"], "page_num": retrieved_docs[doc["index"]]["page"]} for doc in reranked_docs]
                })

                # Display citations
                with st.expander("View Citations"):
                    for idx, doc in enumerate(reranked_docs, 1):
                        st.markdown(f'''
                            <span style="color:cyan; font-weight:bold;">Citation {idx}:</span> 
                            {retrieved_docs[doc["index"]]["text"]} 
                            (<a href="#" style="color:orange;">Page: {retrieved_docs[doc["index"]]["page"]}</a>)
                        ''', unsafe_allow_html=True)

            else:
                st.error("Failed to get the answer.")
        except Exception as e:
            st.error(f"Error while connecting to the server: {e}")
else:
    st.info("Please upload a PDF to start chatting.")
