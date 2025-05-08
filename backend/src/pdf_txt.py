import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# === 1. Load ALL .txt files from txt_files ===
docs_dir = "txt_files"
documents = []

for filename in os.listdir(docs_dir):
    if filename.endswith(".txt"):
        with open(os.path.join(docs_dir, filename), "r", encoding="utf-8") as f:
            text = f.read()
            documents.append(Document(page_content=text, metadata={"filename": filename}))

# === 2. Split text into chunks ===
text_splitter = CharacterTextSplitter(chunk_size=600, chunk_overlap=50)
split_docs = text_splitter.split_documents(documents)

# === 3. Create embedding + vector store ===
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(split_docs, embeddings)
retriever = vectorstore.as_retriever()

# === 4. LLaMA + RAG pipeline ===
llm = ChatOllama(base_url="http://10.10.129.80:11435", model="llama3")

prompt = ChatPromptTemplate.from_template("""
Use the following context to answer the question.
Context:
{context}

Question:
{question}
""")

rag_chain = (
    RunnableParallel({
        "context": retriever | RunnablePassthrough(),
        "question": RunnablePassthrough()
    }) | prompt | llm
)

# === 5. Answer a question ===
def answer_question(question: str) -> dict:
    try:
        context_docs = retriever.invoke(question)
        filenames = list({doc.metadata.get("filename", "Unknown") for doc in context_docs})

        response = rag_chain.invoke(question)

        # Debug
        print("\nresponse.content:", response.content)
        print("\nsources:", filenames)


        return {
            "answer": str(response),  
            "sources": filenames              
        }

    except Exception as e:
        print('🔥 ERROR in rag_chain:', e)
        return {
            "answer": "Something went wrong",
            "sources": []
        }

