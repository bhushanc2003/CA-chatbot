import os
import streamlit as st
from dotenv import load_dotenv
from langchain_qdrant import QdrantVectorStore
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from prompt import prompt

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="CA Bot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "vector_db" not in st.session_state:
    st.session_state.vector_db = None
if "llm" not in st.session_state:
    st.session_state.llm = None

@st.cache_resource
def initialize_models():
    """Initialize the embedding model, vector database, and LLM"""
    try:
        # Vector Embeddings (OpenAI)
        embedding_model = OpenAIEmbeddings(
            model="text-embedding-3-small"
        )
        
        # Connect to Qdrant
        vector_db = QdrantVectorStore.from_existing_collection(
            url="http://localhost:6333",
            collection_name="learning_vectors_openai",
            embedding=embedding_model
        )
        
        # GPT-4 Chat Model
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.7,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        return vector_db, llm, True
    except Exception as e:
        return None, None, str(e)

def process_query(query, vector_db, llm):
    """Process user query and return response"""
    try:
        # Fetch top 2 most relevant documents
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
        messages = [system_message] + st.session_state.conversation_history + [user_message]
        
        # Send message to GPT-4
        response = llm.invoke(messages)
        response_text = response.content
        
        # Update conversation history (keep last 10 exchanges)
        st.session_state.conversation_history.append(user_message)
        st.session_state.conversation_history.append(response)
        
        # Keep only last 20 messages to prevent context overflow
        if len(st.session_state.conversation_history) > 20:
            st.session_state.conversation_history = st.session_state.conversation_history[-20:]
        
        return response_text, True
    except Exception as e:
        return f"Error: {e}", False

# Main UI
st.title("🤖 CA Bot")
st.markdown("---")

# Initialize models
if st.session_state.vector_db is None or st.session_state.llm is None:
    with st.spinner("Initializing CA Bot..."):
        vector_db, llm, init_result = initialize_models()
        
        if vector_db and llm:
            st.session_state.vector_db = vector_db
            st.session_state.llm = llm
            st.success("✅ CA Bot initialized successfully!")
        else:
            st.error(f"❌ Failed to initialize CA Bot: {init_result}")
            st.info("Please check your OpenAI API key and Qdrant connection.")
            st.stop()

# Chat container
chat_container = st.container()

# Display chat messages (from bottom to top)
with chat_container:
    if st.session_state.messages:
        # Reverse the order to show newest messages at bottom
        for message in st.session_state.messages:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.write(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.write(message["content"])

# Chat input at the bottom
if user_input := st.chat_input("Ask me anything about your documents..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    
    # Process the query
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text, success = process_query(
                user_input, 
                st.session_state.vector_db, 
                st.session_state.llm
            )
        
        if success:
            st.write(response_text)
            # Add assistant response to chat
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        else:
            st.error(response_text)

# Sidebar with sample questions
with st.sidebar:
    st.header("💡 Sample Questions")
    
    sample_questions = [
        "What are the key accounting principles?",
        "Explain depreciation methods",
        "What is the difference between GAAP and IFRS?",
        "How do you calculate working capital?",
        "What are the components of financial statements?",
        "Explain revenue recognition principles",
        "What is internal auditing?",
        "How do you prepare a cash flow statement?",
        "What are the types of business expenses?",
        "Explain cost accounting methods"
    ]
    
    for question in sample_questions:
        if st.button(question, key=f"sample_{question}", use_container_width=True):
            # Add the sample question as if user typed it
            st.session_state.messages.append({"role": "user", "content": question})
            
            # Process the query
            response_text, success = process_query(
                question, 
                st.session_state.vector_db, 
                st.session_state.llm
            )
            
            if success:
                st.session_state.messages.append({"role": "assistant", "content": response_text})
            else:
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {response_text}"})
            
            st.rerun()
    
    st.markdown("---")
    
    # Display conversation stats
    st.subheader("📊 Session Stats")
    st.metric("Messages Exchanged", len(st.session_state.messages))
    st.metric("Context History", len(st.session_state.conversation_history))
    
    # Clear conversation button
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Powered by OpenAI GPT-4 & Qdrant Vector Database"
    "</div>", 
    unsafe_allow_html=True
)