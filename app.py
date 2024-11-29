import logging
from flask import Flask, render_template, request, jsonify
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin 
import os
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for the app
CORS(app) 

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(message)s', 
    handlers=[
        logging.FileHandler("question_logs.log"),  # Log to a file
        logging.StreamHandler()  # Also log to the console
    ]
)

# Load API keys from environment variables
groq_api_key = os.getenv("GROQ_API_KEY")
google_api_key = os.getenv("GOOGLE_API_KEY")

# Set the Google API key in the environment (needed for certain libraries)
os.environ["GOOGLE_API_KEY"] = google_api_key

# Initialize LLM model
llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")

# Define prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer questions up to given content.
    <context>{context}</context>
    {input}
    """
)

# Initialize embeddings, loader, and FAISS vector store
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
loader = PyPDFDirectoryLoader("public/data")

# Load documents and split them into chunks
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
final_documents = text_splitter.split_documents(docs[:20])

# Build FAISS index from documents
vectors = FAISS.from_documents(final_documents, embeddings)

@app.route("/get_answer", methods=["POST"])
def get_answer():
    data = request.json  # Get JSON data
    
    question = data.get("question", "")  # Access 'question' from JSON payload
    if question:
        # Create document chain and retrieval chain
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Measure response time
        start = time.process_time()
        
        # Get the response using the retrieval chain
        response = retrieval_chain.invoke({"input": question})
        
        # Log the response time
        print("Response time: ", time.process_time() - start)
        
        # Extract and return the answer
        answer = response.get("answer", "No answer found.")
        
        # Log the question and answer
        logging.info(f"Question: {question} | Answer: {answer}")
        
        return jsonify({"answer": answer})
    else:
        # If no question is provided, return an error
        return jsonify({"error": "No question provided"}), 400

@app.route("/check_connection", methods=["GET"])
def check_connection():
    try:
        # Check if everything is working, like the model connection
        return jsonify({"status": "connected"})
    except Exception as e:
        return jsonify({"status": "disconnected", "error": str(e)}), 500


if __name__ == "__main__":
    # Run the app on localhost with port 5001
    app.run(debug=True, host='0.0.0.0', port=5001)
