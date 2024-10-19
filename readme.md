# Deployment Instructions using Docker

## Prerequisites
Before you begin, ensure you have the following installed on your machine:
- **Docker**: Install Docker from [Docker's official website](https://www.docker.com/)
- **Git**: Download and install Git from [Git's official website](https://git-scm.com/)
- **API Keys** for Pinecone, Cohere, and OpenAI

## Clone the Repository
1. Open a terminal
2. Clone the repository using Git:
   ```bash
   git clone https://github.com/Sushmita10062002/chatbot.git
   ```

## Set Up Environment Variables
In the backend folder, create a .env file and add the following environment variables:
```
PINECONE_API_KEY=<your_pinecone_api_key>
COHERE_API_KEY=<your_cohere_api_key>
OPENAI_API_KEY=<your_openai_api_key>
```

In the frontend folder, create a .env file and add the following environment variables:
```
OPENAI_API_KEY=<your_openai_api_key>
PDF_PROCESSING_API="http://backend:8000/process_pdf"
GET_RELEVANT_DOCS="http://backend:8000/get_retrieved_docs"
GET_RERANKED_DOCS="http://backend:8000/get_reranked_docs"
```

## Build and Run the Docker Containers
Build the Docker image and start the containers using Docker Compose. Run this command in the folder where docker-compose.yaml exists:
```bash
docker-compose up --build
```

## Stopping the Services
To stop the services, you can press CTRL+C in the terminal where Docker is running. Alternatively, you can run:
```bash
docker-compose down
```

## Accessing the Applications
- Open your browser and navigate to http://localhost:8000 for the FastAPI application (if applicable)
- Navigate to http://localhost:8501 for the Streamlit application

## Usage
Once the applications are running, you can upload PDF files and interact with the chatbot by asking questions related to the content of the PDFs.
