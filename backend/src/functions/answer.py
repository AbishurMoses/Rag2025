import os
import torch
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging

# Configure logging
logger = logging.getLogger(__name__)

def format_docs_with_filenames(docs: list[Document]) -> str:
    """
    Formats a list of Document objects to include their filename and page content.
    """
    formatted_docs = []
    for i, doc in enumerate(docs):
        filename = doc.metadata.get("filename", "Unknown source")
        formatted_docs.append(f"Source Filename: {filename}\nContent:\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted_docs)

def answer_question(question: str) -> dict:
    """
    Uses GPU acceleration for embeddings to answer questions based on document context.
    
    Args:
        question (str): The question to answer
        
    Returns:
        dict: A dictionary containing the answer and source filenames.
              - answer (str): The generated answer or an error message.
              - sources (list): List of filenames used as context.
    """
    try:
        logger.info(f"Starting answer_question with question: {question}")
        
        # === 1. Load ALL .txt files from context ===
        docs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "context"))
        logger.info(f"Checking directory: {docs_dir}")
        documents = []

        if not os.path.exists(docs_dir):
            logger.error(f"Directory '{docs_dir}' does not exist")
            return {"answer": f"Directory '{docs_dir}' does not exist", "sources": []}

        for filename in os.listdir(docs_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(docs_dir, filename)
                logger.info(f"Processing file: {filename}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()
                        documents.append(Document(page_content=text, metadata={"filename": filename}))
                except Exception as e:
                    logger.error(f"Error reading {filename}: {e}")
                    continue

        if not documents:
            logger.error(f"No .txt files found in '{docs_dir}'")
            return {"answer": f"No .txt files found in '{docs_dir}'", "sources": []}

        # === 2. Split text into chunks ===
        text_splitter = CharacterTextSplitter(
            chunk_size=3000,
            chunk_overlap=50,
            separator="\n\n"
        )
        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Created {len(split_docs)} document chunks")

        # === 3. Create GPU-accelerated embedding + vector store ===
        # Check if GPU is available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cuda":
            logger.info(f"Using GPU acceleration for embeddings: {torch.cuda.get_device_name(0)}")
        else:
            logger.warning("GPU not available, falling back to CPU for embeddings")
            
        # Configure embedding model with the appropriate device
        model_kwargs = {'device': device.type}
        encode_kwargs = {'device': device.type, 'batch_size': 32}  # Increase batch size for GPU
        
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs
        )
        
        # Create vector store
        vectorstore = FAISS.from_documents(split_docs, embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})  # Retrieve top 5 most relevant chunks

        # === 4. LLaMA + RAG pipeline ===
        # http://10.10.129.80:11435 ABISHUR
        llm = ChatOllama(base_url="http://localhost:54323/:11435", model="llama3")
        
        prompt = ChatPromptTemplate.from_template("""
        Use the following context to answer the question.
        When citing information, refer to the 'Source Filename' provided with the context.

        Context:
        {context}

        Question:
        {question}

        Answer:""")

        # RAG chain with GPU-accelerated embeddings
        rag_chain = (
            RunnableParallel({
                "context": retriever | RunnableLambda(format_docs_with_filenames),
                "question": RunnablePassthrough()
            })
            | prompt
            | llm
        )

        # === 5. Answer the question ===
        context_docs_for_source_list = retriever.invoke(question)
        filenames = sorted(list(set(doc.metadata.get("filename", "Unknown") for doc in context_docs_for_source_list)))

        response_obj = rag_chain.invoke(question)
        answer_content = response_obj.content if hasattr(response_obj, 'content') else str(response_obj)

        # Debug
        logger.info("\nLLM Response: " + answer_content[:100] + "...")
        logger.info(f"Sources: {filenames}")

        result = {
            "answer": answer_content,
            "sources": filenames
        }
        return result

    except Exception as e:
        import traceback
        logger.error(f'Error in answer_question: {e}')
        logger.error(traceback.format_exc())
        return {
            "answer": f"Something went wrong: {str(e)}",
            "sources": []
        }