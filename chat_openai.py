import os
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompt import prompt

load_dotenv()

# Vector Embeddings (OpenAI)
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small"  # or "text-embedding-3-large"
)

# Connect to Qdrant
vector_db = QdrantVectorStore.from_existing_collection(
    url="http://localhost:6333",
    collection_name="learning_vectors_openai",
    embedding=embedding_model
)

# GPT-4 Chat Model
llm = ChatOpenAI(
    model="gpt-4o",  # or "gpt-4-turbo" or "gpt-4"
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

print("🤖 GPT-4 Chatbot is ready! Type 'exit' to quit.\n")

# Store conversation history
conversation_history = []

# --- Main loop ---
while True:
    query = input("> ")
    if query.lower() in ["exit", "quit"]:
        print("👋 Exiting chat...")
        break

    # Fetch ONLY top 2 most relevant documents
    search_results = vector_db.similarity_search(query=query, k=2)

    # Build context from top results
    context = "\n\n\n".join([
        f"Page Content: {result.page_content}\n"
        f"Page Number: {result.metadata.get('page_label', 'N/A')}\n"
        f"File Location: {result.metadata.get('source', 'N/A')}"
        for result in search_results
    ])

    # Create messages
    system_message = SystemMessage(content=f"""
    {prompt}

    Context:
    {context}
    """)
    
    user_message = HumanMessage(content=query)
    
    # Prepare messages with conversation history
    messages = [system_message] + conversation_history + [user_message]

    try:
        # Send message to GPT-4
        response = llm.invoke(messages)
        
        # Extract response content
        response_text = response.content
        
        # Update conversation history (keep last 10 exchanges to manage context)
        conversation_history.append(user_message)
        conversation_history.append(response)
        
        # Keep only last 10 messages to prevent context overflow
        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]
        
        print(f"\n🤖: {response_text}\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your OpenAI API key and try again.\n")