from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Load environment variables
load_dotenv()

# Path to Resources folder
resources_path = Path(__file__).parent / "Resources"

# Load all PDFs from Resources folder
all_docs = []
for pdf_file in resources_path.glob("*.pdf"):
    print(f"📂 Loading: {pdf_file.name}")
    loader = PyPDFLoader(file_path=pdf_file)
    docs = loader.load()
    all_docs.extend(docs)

print(f"✅ Loaded {len(all_docs)} documents from {resources_path}")

# Split into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=400
)
split_docs = text_splitter.split_documents(all_docs)

# OpenAI Embeddings (GPT-4 compatible)
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"  # or "text-embedding-3-large" for better quality
)

# Store in Qdrant
vector_store = QdrantVectorStore.from_documents(
    documents=split_docs,
    url="http://localhost:6333",  # Qdrant running locally
    collection_name="learning_vectors_openai",
    embedding=embedding_model
)

print("🎉 Indexing of ALL PDFs in Resources folder done with OpenAI Embeddings ✅")