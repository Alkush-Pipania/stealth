# Graph RAG Pipeline - Setup Steps

## Step 1: Run Neo4j & Redis with Docker Compose

```bash
docker-compose up -d
```

Access Neo4j Browser at: http://localhost:7474
- Username: `neo4j`
- Password: `password`

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create `.env` file in project root:

```bash
# Google API Key
GOOGLE_API_KEY=your_google_api_key

# LlamaParse
LLAMA_CLOUD_API_KEY=your_llama_api_key

# Neo4j (matches docker-compose.yml)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_HOST_URL=your_pinecone_host
pinecone_environment=us-east-1
INDEX=your_index_name

# Azure - Not needed! Just pass public URLs or URLs with SAS tokens already in them
# Your blob URLs work directly: https://2alabs.blob.core.windows.net/document/file.pdf
```

## Step 4: Start FastAPI Server

```bash
uvicorn app.main:app --reload
```

## Step 5: Test in Swagger UI

1. Open: http://localhost:8000/api/docs
2. Find POST `/api/v1/embed/embed`
3. Click "Try it out"
4. Enter:
   ```json
   {
     "user_id": "your_user_id",
     "azure_url": "https://yourblob.blob.core.windows.net/container/doc.pdf"
   }
   ```
5. Click "Execute"

## API Keys You Need

1. **Google AI Studio**: https://makersuite.google.com/app/apikey
2. **LlamaIndex Cloud**: https://cloud.llamaindex.ai/api-key
3. **Pinecone**: https://app.pinecone.io/ (create index with dimension 3072)
4. **Azure**: Generate SAS token from Azure Portal

## That's It! 🚀

