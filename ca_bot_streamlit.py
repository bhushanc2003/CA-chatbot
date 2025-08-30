import streamlit as st
import os
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
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background-color: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #1565c0;
    }
</style>
""", unsafe_allow_html=True)

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
        
        return embedding_model, vector_db, llm
    except Exception as e:
        st.error(f"Error initializing models: {str(e)}")
        return None, None, None

def get_bot_response(query, vector_db, llm, conversation_history):
    """Get response from the CA bot"""
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
        messages = [system_message] + conversation_history + [user_message]
        
        # Send message to GPT-4
        response = llm.invoke(messages)
        
        return response.content, user_message, response
        
    except Exception as e:
        return f"❌ Error: {str(e)}\nPlease check your OpenAI API key and Qdrant connection.", None, None

def main():
    # Header
    st.markdown('<h1 class="main-header">🧮 CA Bot</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Ask me any query related to Chartered Accountancy, Taxation, Auditing, and Financial Regulations</p>', unsafe_allow_html=True)
    
    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Initialize models
    with st.spinner("🔄 Initializing CA Bot..."):
        embedding_model, vector_db, llm = initialize_models()
    
    if vector_db is None or llm is None:
        st.error("Failed to initialize the bot. Please check your configuration.")
        return
    
    # Sidebar with information
    with st.sidebar:
        st.header("📋 About CA Bot")
        st.write("""
        This AI assistant specializes in:
        - **Taxation** queries and compliance
        - **Auditing** standards and procedures
        - **Financial** accounting principles
        - **Regulatory** requirements
        - **CA exam** preparation
        """)
        
        st.header("💡 Sample Questions")
        sample_questions = [
            "What are the key provisions of GST?",
            "Explain audit procedures for inventory",
            "What is the due date for filing ITR?",
            "Difference between direct and indirect tax",
            "CA final exam preparation tips"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"sample_{question}"):
                st.session_state.user_input = question
        
        st.header("🗑️ Actions")
        if st.button("Clear Chat History"):
            st.session_state.conversation_history = []
            st.session_state.chat_messages = []
            st.rerun()
    
    # Main chat interface
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "💬 Ask your CA-related question:",
            key="user_input",
            placeholder="e.g., What are the latest changes in income tax rules?"
        )
    
    with col2:
        ask_button = st.button("Ask 🚀", type="primary")
    
    # Process user input
    if ask_button and user_input:
        with st.spinner("🤔 Thinking..."):
            response_text, user_message, bot_response = get_bot_response(
                user_input, vector_db, llm, st.session_state.conversation_history
            )
            
            if user_message and bot_response:
                # Update conversation history
                st.session_state.conversation_history.append(user_message)
                st.session_state.conversation_history.append(bot_response)
                
                # Keep only last 20 messages to prevent context overflow
                if len(st.session_state.conversation_history) > 20:
                    st.session_state.conversation_history = st.session_state.conversation_history[-20:]
                
                # Add to chat messages for display
                st.session_state.chat_messages.append(("user", user_input))
                st.session_state.chat_messages.append(("bot", response_text))
            else:
                st.session_state.chat_messages.append(("user", user_input))
                st.session_state.chat_messages.append(("bot", response_text))
        
        # Rerun to refresh the interface
        st.rerun()
    
    # Display chat history
    if st.session_state.chat_messages:
        st.markdown("---")
        st.header("💬 Chat History")
        
        # Display messages in reverse order (newest first)
        for i, (sender, message) in enumerate(reversed(st.session_state.chat_messages)):
            if sender == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 You:</strong><br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 CA Bot:</strong><br>
                    {message}
                </div>
                """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>🔒 Powered by OpenAI GPT-4 & Qdrant Vector Database</p>
        <p>💡 For accurate and up-to-date CA information</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()