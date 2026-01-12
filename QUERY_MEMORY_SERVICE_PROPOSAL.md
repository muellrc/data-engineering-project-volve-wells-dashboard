# Feature Proposal: Intelligent Query Memory Service

## Overview

**Name**: Intelligent Query Memory Service (IQMS)  
**Purpose**: Enhance the NLQ Service with vector-based query caching, similarity search, and learning from past queries to improve performance, reduce costs, and improve SQL generation quality.

## Problem Statement

Current NLQ Service limitations:
- Every query calls the LLM, even for similar questions
- No learning from past successful queries
- No query suggestions or autocomplete
- Higher latency and cost for repeated/similar queries
- No historical query analytics

## Proposed Solution

A new microservice that:
1. Stores all NLQ queries with embeddings in a vector database
2. Performs semantic similarity search to find similar past queries
3. Returns cached SQL for highly similar queries (fast path)
4. Provides few-shot examples for improved SQL generation
5. Offers query suggestions and autocomplete
6. Tracks query performance and success rates

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Intelligent Query Memory Service                │
│                    (Vector DB Integration)                  │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Chroma     │   │  Embedding   │   │  Query       │
│  Vector DB   │   │  Generator   │   │  Analytics   │
│              │   │              │   │              │
│ • Query      │   │ • OpenAI     │   │ • Success    │
│   Embeddings │   │   Embeddings │   │   Tracking   │
│ • SQL Cache  │   │ • Local      │   │ • Usage      │
│ • Metadata   │   │   (sentence- │   │   Patterns   │
│              │   │   transformers)│              │
└──────────────┘   └──────────────┘   └──────────────┘
        │
        │ Integrates with
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    NLQ Service (Enhanced)                    │
│                                                              │
│  1. Receive query                                            │
│  2. Check IQMS for similar queries                          │
│  3. If similarity > 0.95: Return cached SQL (fast path)      │
│  4. If similarity > 0.85: Use as few-shot examples          │
│  5. Generate new SQL with context                           │
│  6. Store in IQMS for future use                            │
└─────────────────────────────────────────────────────────────┘
```

## Embedding Provider Support

The Query Memory Service supports multiple embedding providers:

### 1. OpenAI Embeddings (Cloud)
- **Model**: `text-embedding-3-small` (cost-effective) or `text-embedding-3-large` (higher quality)
- **Pros**: High quality, fast, reliable
- **Cons**: Requires API key, costs per embedding
- **Use Case**: Production deployments with budget for embeddings

### 2. Sentence Transformers (Local)
- **Model**: `all-MiniLM-L6-v2` (default) or `all-mpnet-base-v2` (higher quality)
- **Pros**: Free, no API calls, privacy-preserving, works offline
- **Cons**: Requires model download (~80MB), slightly slower first run
- **Use Case**: Privacy-sensitive deployments, cost reduction, offline capability

### 3. Ollama Embeddings (Local, Experimental)
- **Note**: Ollama doesn't have a dedicated embeddings API, but some models can generate embeddings
- **Alternative**: Use sentence-transformers for embeddings, Ollama for SQL generation
- **Use Case**: When using Ollama for LLM, use sentence-transformers for embeddings

**Recommended Configuration:**
- **Development/Testing**: sentence-transformers (free, no API key needed)
- **Production (Privacy-sensitive)**: sentence-transformers
- **Production (High Quality)**: OpenAI `text-embedding-3-small`

## Technical Implementation

### Service Structure

```
query_memory_service/
├── __init__.py
├── api.py                    # FastAPI REST API
├── vector_store.py           # Chroma/Qdrant integration
├── embedding_service.py      # Multi-provider embedding generation
├── query_cache.py            # Caching logic
├── analytics.py              # Query analytics
├── database.py               # PostgreSQL for metadata
├── Dockerfile
├── requirements.txt
├── README.md
├── LEARNING_GUIDE.md
└── TESTING.md
```

### Core Components

#### 1. Embedding Service (`embedding_service.py`)

```python
"""
Generates embeddings for natural language queries.
Supports multiple embedding providers: OpenAI, sentence-transformers (local).
"""
import os
from typing import List, Optional
from enum import Enum

class EmbeddingProvider(str, Enum):
    OPENAI = "openai"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    # Note: Ollama doesn't have embeddings API, use sentence-transformers instead

class EmbeddingService:
    """Generates embeddings for queries."""
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("EMBEDDING_PROVIDER", "sentence_transformers")
        self._init_provider()
    
    def _init_provider(self):
        """Initialize embedding provider."""
        if self.provider == EmbeddingProvider.OPENAI:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.model = SentenceTransformer(model_name)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.provider == EmbeddingProvider.OPENAI:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        elif self.provider == EmbeddingProvider.SENTENCE_TRANSFORMERS:
            return self.model.encode(text).tolist()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
```

#### 2. Vector Store (`vector_store.py`)

```python
"""
Vector database integration for query storage and similarity search.
Uses Chroma for vector storage and similarity search.
"""
from chromadb import Client, Settings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

class QueryVectorStore:
    """Manages query embeddings and similarity search."""
    
    def __init__(self, persist_directory: str = "/app/data/chroma_db"):
        self.client = Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory
        ))
        self.collection = self.client.get_or_create_collection(
            name="nlq_queries",
            metadata={"hnsw:space": "cosine"}
        )
    
    def store_query(
        self,
        question: str,
        embedding: List[float],
        sql: str,
        execution_time_ms: float,
        success: bool,
        result_count: int,
        model_info: Dict[str, str]
    ) -> str:
        """Store a query with its embedding and metadata."""
        query_id = str(uuid.uuid4())
        
        self.collection.add(
            embeddings=[embedding],
            documents=[question],
            metadatas=[{
                "sql": sql,
                "execution_time_ms": execution_time_ms,
                "success": success,
                "result_count": result_count,
                "model_provider": model_info.get("provider"),
                "model_name": model_info.get("model"),
                "timestamp": datetime.now().isoformat(),
                "query_id": query_id
            }],
            ids=[query_id]
        )
        
        return query_id
    
    def find_similar_queries(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find similar queries using vector similarity search."""
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        similar_queries = []
        for i, distance in enumerate(results['distances'][0]):
            similarity = 1 - distance  # Convert distance to similarity
            
            if similarity >= min_similarity:
                similar_queries.append({
                    "question": results['documents'][0][i],
                    "sql": results['metadatas'][0][i]['sql'],
                    "similarity": similarity,
                    "execution_time_ms": results['metadatas'][0][i]['execution_time_ms'],
                    "success": results['metadatas'][0][i]['success'],
                    "timestamp": results['metadatas'][0][i]['timestamp'],
                    "query_id": results['ids'][0][i]
                })
        
        return similar_queries
```

#### 3. Query Cache (`query_cache.py`)

```python
"""
Intelligent caching layer for NLQ queries.
Implements similarity-based caching with configurable thresholds.
"""
from typing import Dict, Any, Optional, List
from .vector_store import QueryVectorStore
from .embedding_service import EmbeddingService

class QueryCache:
    """Manages query caching and retrieval."""
    
    def __init__(self):
        self.vector_store = QueryVectorStore()
        self.embedding_service = EmbeddingService()
        self.cache_threshold_high = 0.95  # Return cached SQL
        self.cache_threshold_medium = 0.85  # Use as examples
    
    def get_cached_query(
        self,
        question: str
    ) -> Optional[Dict[str, Any]]:
        """Check if query exists in cache with high similarity."""
        embedding = self.embedding_service.generate_embedding(question)
        similar = self.vector_store.find_similar_queries(
            embedding,
            top_k=1,
            min_similarity=self.cache_threshold_high
        )
        
        if similar:
            return {
                "cached": True,
                "sql": similar[0]['sql'],
                "similarity": similar[0]['similarity'],
                "source_query": similar[0]['question']
            }
        return None
    
    def get_few_shot_examples(
        self,
        question: str,
        max_examples: int = 3
    ) -> List[Dict[str, str]]:
        """Get similar queries to use as few-shot examples."""
        embedding = self.embedding_service.generate_embedding(question)
        similar = self.vector_store.find_similar_queries(
            embedding,
            top_k=max_examples,
            min_similarity=self.cache_threshold_medium
        )
        
        # Filter to only successful queries
        successful = [q for q in similar if q['success']]
        
        return [
            {
                "question": q['question'],
                "sql": q['sql']
            }
            for q in successful[:max_examples]
        ]
    
    def store_query(
        self,
        question: str,
        sql: str,
        execution_time_ms: float,
        success: bool,
        result_count: int,
        model_info: Dict[str, str]
    ) -> str:
        """Store query in vector database."""
        embedding = self.embedding_service.generate_embedding(question)
        
        return self.vector_store.store_query(
            question=question,
            embedding=embedding,
            sql=sql,
            execution_time_ms=execution_time_ms,
            success=success,
            result_count=result_count,
            model_info=model_info
        )
```

## Docker Configuration

Add to `docker-compose.yaml`:

```yaml
dev-query-memory-service:
  build:
    context: ./query_memory_service
  depends_on:
    dev-postgres-db:
      condition: service_healthy
    dev-ollama:
      condition: service_started  # Optional, only if using Ollama for LLM
  environment:
    - EMBEDDING_PROVIDER=${EMBEDDING_PROVIDER:-sentence_transformers}
    - EMBEDDING_MODEL=${EMBEDDING_MODEL:-all-MiniLM-L6-v2}
    - OPENAI_API_KEY=${OPENAI_API_KEY:-}  # Only if using OpenAI embeddings
    - CHROMA_PERSIST_DIR=/app/data/chroma_db
  ports:
    - "8002:8002"
  volumes:
    - query-memory-data:/app/data/chroma_db
  restart: unless-stopped

volumes:
  query-memory-data:
```

## Integration with NLQ Service

Modify `nlq_service/api.py` to integrate with IQMS:

```python
# Add to nlq_service/api.py

from query_memory_service.query_cache import QueryCache

# Initialize cache
query_cache = QueryCache()

@app.post("/query", response_model=QueryResponse)
async def execute_natural_language_query(request: QueryRequest):
    start_time = time.time()
    
    # Step 1: Check cache for exact/similar query
    cached = query_cache.get_cached_query(request.question)
    if cached and cached['similarity'] > 0.95:
        # Fast path: return cached SQL
        results = db_manager.execute_query(cached['sql'])
        execution_time = (time.time() - start_time) * 1000
        
        return QueryResponse(
            question=request.question,
            sql=cached['sql'],
            explanation=f"Cached query (similarity: {cached['similarity']:.2%})",
            results=results,
            row_count=len(results),
            execution_time_ms=execution_time,
            cached=True
        )
    
    # Step 2: Get few-shot examples if available
    examples = query_cache.get_few_shot_examples(request.question)
    
    # Step 3: Generate SQL with examples
    schema_context = db_manager.get_database_schema_context()
    llm_result = llm_client.generate_sql(
        natural_language_query=request.question,
        schema_context=schema_context,
        examples=examples  # Pass examples to LLM
    )
    
    # ... rest of existing logic ...
    
    # Step 4: Store query in cache
    query_cache.store_query(
        question=request.question,
        sql=sanitized_sql,
        execution_time_ms=execution_time,
        success=True,
        result_count=len(results),
        model_info={
            "provider": llm_result.get("provider"),
            "model": llm_result.get("model")
        }
    )
    
    return QueryResponse(...)
```

## LLM Provider Integration

The Query Memory Service works with all LLM providers used by NLQ Service:

- **OpenAI**: Works with GPT-4o-mini, GPT-4, etc.
- **Anthropic**: Works with Claude 3.5 Sonnet, etc.
- **Ollama**: Works with llama3.1, mistral, codellama, etc.

**Note**: The embedding provider is independent of the LLM provider. You can use:
- OpenAI embeddings + OpenAI LLM
- OpenAI embeddings + Ollama LLM (cost-effective SQL generation)
- sentence-transformers embeddings + Ollama LLM (fully local, no API costs)
- sentence-transformers embeddings + OpenAI LLM (local embeddings, cloud LLM)

## Benefits

1. **Performance**
   - 10-100x faster for cached queries (no LLM call)
   - Reduced latency for similar queries

2. **Cost Reduction**
   - Fewer LLM API calls (major cost savings)
   - Embedding API calls are cheaper than completion calls
   - Local embeddings (sentence-transformers) = zero cost

3. **Quality Improvement**
   - Better SQL generation via few-shot examples
   - Learning from successful queries
   - Pattern recognition across query history

4. **User Experience**
   - Query suggestions/autocomplete
   - Faster responses
   - Query history and analytics

5. **Analytics**
   - Track popular queries
   - Identify query patterns
   - Monitor success rates

## Technical Stack

- **Vector database**: Chroma (lightweight, Python-native, persistent storage)
- **Embeddings**: 
  - OpenAI `text-embedding-3-small` (cloud, high quality)
  - sentence-transformers `all-MiniLM-L6-v2` (local, free, privacy-preserving)
- **Framework**: FastAPI
- **Storage**: Persistent Chroma DB (Docker volume)

## Implementation Phases

### Phase 1: Core caching (MVP)
- Vector store setup
- Embedding generation (sentence-transformers for local)
- Similarity search
- Cache check/store endpoints
- NLQ Service integration

### Phase 2: Enhancements
- Few-shot example retrieval
- Query suggestions endpoint
- Analytics dashboard
- Performance metrics
- OpenAI embeddings support

### Phase 3: Advanced features
- Query clustering
- Automatic query optimization
- User-specific query history
- Query performance recommendations
- Multi-embedding provider comparison

## Learning Value

Demonstrates:
- Vector database integration (Chroma)
- Embedding generation (OpenAI, sentence-transformers)
- Semantic similarity search
- Semantic caching patterns
- RAG with query history
- Few-shot learning implementation
- Performance optimization techniques
- Multi-provider architecture (embeddings + LLMs)

## Next Steps

1. Create `query_memory_service/` directory structure
2. Implement core components (vector_store, embedding_service, query_cache)
3. Build REST API endpoints
4. Integrate with NLQ Service
5. Add Docker configuration
6. Create documentation and learning guide
