# CA Chatbot

A local chatbot for querying CA (Chartered Accountant) resources using GPT-4 and Qdrant vector database.

## Features

- Indexes all PDF files in the `Resources` folder using OpenAI embeddings.
- Stores document vectors in Qdrant for fast semantic search.
- Chatbot answers queries using GPT-4 and relevant document context.

## Setup

### 1. Clone the repository

```sh
git clone <repo-url>
cd CA chatbot
```

### 2. Install dependencies

```sh
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key
```

### 4. Start Qdrant (Vector DB)

You can run Qdrant locally using Docker:

```sh
docker-compose up -d
```

Qdrant will be available at `http://localhost:6333`.

### 5. Index PDF documents

Run the indexing script to process all PDFs in the `Resources` folder:

```sh
python indexing_openai.py
```

### 6. Start the chatbot

```sh
python chat_openai.py
```

### 7. Start the bot with UI

```sh
streamlit run ca_bot_streamlit.py
```

Type your questions in the terminal. Type `exit` to quit.

## Folder Structure

- `Resources/` — Place all PDF documents here.
- `indexing_openai.py` — Indexes PDFs and stores vectors in Qdrant.
- `chat_openai.py` — Chatbot interface using GPT-4 and Qdrant.
- `requirements.txt` — Python dependencies.
- `docker-compose.yml` — Qdrant setup.

## Notes

- Requires an OpenAI API key for embeddings and chat.
- Qdrant must be running locally for vector search.
- For best results, use GPT-4 or GPT-4o