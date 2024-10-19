from fastapi import FastAPI, UploadFile, File
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import cohere
import uuid
import os
import io
import time
load_dotenv(dotenv_path="./.env")

# Initialization
client = OpenAI()
app = FastAPI()
co = cohere.ClientV2(os.environ.get("COHERE_API_KEY"))

splitter = RecursiveCharacterTextSplitter()
splitter._chunk_size = 1000
splitter._chunk_overlap = 0
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("sampleset")

# Pydantic models for request/response validation
class ReRankRequest(BaseModel):
    question: str
    docs: list[str]


class RetrieverInputData(BaseModel):
    question: str
    pdf_id: str


def add_embeddings(chunks: list):
    text_to_embed = [chunk["text"] for chunk in chunks]
    embeddings = client.embeddings.create(input = text_to_embed, model = "text-embedding-3-small").data
    for i in range(len(chunks)):
        value = chunks[i]
        chunks[i] = {
            "id": str(uuid.uuid4()),
            "values": embeddings[i].embedding,
            "metadata": value
        }
    print(len(chunks))
    index.upsert(chunks, batch_size=100)


@app.post("/get_reranked_docs")
async def rerank_docs(input_data: ReRankRequest):
    try:
        response = co.rerank(model = "rerank-english-v3.0",
                query = input_data.question, 
                documents = input_data.docs,
                top_n = 3)
        reranked_docs = [{"index": result.index, "relevance_score": result.relevance_score} for result in response.results]
        print(reranked_docs)
        return {"reranked_docs": reranked_docs}
    except Exception as e:
        return {"reranked_docs": [{"index": i, "relevance_score": 0} for i in range(len(input_data.docs))]}

@app.post("/process_pdf")
async def process_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.pdf'):
        return {"error": "Invalid file type"}, 500

    try: 
        content = await file.read()
        pdf_file = io.BytesIO(content)
        reader = PdfReader(pdf_file)
        pdf_id = str(uuid.uuid4())
        num_pages = len(reader.pages)
        chunks = []

        for page_num in range(num_pages):
            content = reader.pages[page_num].extract_text()
            page_splits = splitter.split_text(content)
            for split in page_splits:
                chunks.append({
                    "text": split, 
                    "source": file.filename,
                    "pdf_id": pdf_id,
                    "page": page_num + 1
                })
        add_embeddings(chunks)
        time.sleep(3)
        return {"success": "Pdf processed successfully", "pdf_id": pdf_id}
    except:
        return {"error": "Failed to process pdf"}, 500
  

@app.post("/get_retrieved_docs")
async def get_retrieved_docs(input_data: RetrieverInputData):
    try:
        print(input_data.question)
        query_vector = client.embeddings.create(input=input_data.question, model="text-embedding-3-small").data[0].embedding
        retrieved_docs = index.query(
                vector=query_vector,
                filter={
                    "pdf_id": {"$eq": input_data.pdf_id}
                },
                top_k=5,
                include_metadata=True)["matches"]
        print(retrieved_docs)
        
        return {"retrieved_docs": [doc["metadata"] for doc in retrieved_docs]}
    except Exception as e:
        return {"retrieved_docs": []}


        


