import logging
from flask import Flask, request, jsonify
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from flask_cors import CORS
import os
import time

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # Ensure JSON responses are not ASCII-encoded

# Enable CORS for the app
CORS(app, resources={r"/*": {"origins": "https://alicenkbaytop.github.io"}})

# Set up logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler("question_logs.log"),  # Log to a file
        logging.StreamHandler(),  # Also log to the console
    ],
)

# Initialize API keys
google_api_key = os.getenv("GOOGLE_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize the LLM (Groq)
llm = ChatGroq(
    model="mixtral-8x7b-32768",  # Correct model name
    temperature=0,
    max_tokens=500,  # Limit response length
    timeout=None,
    max_retries=2,
)

# Define prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer the question based on the given context. If the context doesn't contain enough information, say "I can't answer this question."
    Context: {context}
    Question: {input}
    """
)

# Initialize embeddings, loader, and FAISS vector store
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
loader = PyPDFDirectoryLoader("public/data", glob="*.pdf")  # Load only PDF files

# Load documents and split them into chunks
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)  # Smaller chunks
final_documents = text_splitter.split_documents(docs[:20])

# Build FAISS index from documents
vectors = FAISS.from_documents(final_documents, embeddings)

# Save embeddings to disk (if not already saved)
if not os.path.exists("faiss_index"):
    print("Saving FAISS index to disk...")
    vectors.save_local("faiss_index")

# Load embeddings from disk
print("Loading FAISS index from disk...")
vectors = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)


def is_answer_in_context(answer, context):
    """
    Check if the answer is relevant to the context using keyword matching.
    """
    # If answer is a list, convert it to a string
    if isinstance(answer, list):
        answer = " ".join(answer)

    # If context is a list of Document objects, extract their text content
    if isinstance(context, list):
        context = " ".join([doc.page_content for doc in context])

    # Check if any keyword from the answer is in the context
    keywords = answer.lower().split()
    context_lower = context.lower()
    return any(keyword in context_lower for keyword in keywords)


@app.route("/get_answer", methods=["POST"])
def get_answer():
    data = request.json  # Get JSON data

    question = data.get("question", "")  # Access 'question' from JSON payload
    if question:
        # Create document chain and retrieval chain
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = vectors.as_retriever(search_kwargs={"k": 3})  # Retrieve only 3 chunks
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        # Measure response time
        start = time.time()

        # Get the response using the retrieval chain
        response = retrieval_chain.invoke(
            {"output_language": "English", "input": question}
        )

        # Log the response time
        response_time = time.time() - start

        # Extract the answer and context
        answer = response.get("answer", "No answer found.")
        context = response.get("context", "")

        # Handle empty or invalid answer/context
        if not answer or not context:
            answer = "I can't answer this question!"
        else:
            # Validate if the answer is relevant to the context
            if not is_answer_in_context(answer, context):
                answer = "I can't answer this question!"

        # Log the question and answer
        logging.info(
            f"Question: {question} | Answer: {answer} | Response Time: {response_time:.2f} seconds"
        )

        return jsonify(
            {"answer": answer, "response_time": f"{response_time:.2f} seconds"}
        )
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
    app.run(debug=True, host="0.0.0.0", port=5001)