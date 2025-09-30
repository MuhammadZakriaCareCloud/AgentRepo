# Database Configuration Recommendations for AI Call System

## Current Setup
The system currently uses SQLite for development. For production and enhanced agent training capabilities, we recommend upgrading to PostgreSQL with additional tools for optimal performance.

## Recommended Production Database Architecture

### 1. Primary Database: PostgreSQL
```python
# settings.py - Production Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ai_call_system',
        'USER': 'ai_call_user',
        'PASSWORD': 'your_secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Connection pooling for better performance
DATABASE_CONNECTION_POOLING = {
    'MAX_CONNS': 20,
    'MIN_CONNS': 5,
}
```

### 2. Why PostgreSQL is Ideal for Agent Training

#### JSON Field Support
PostgreSQL's native JSON support is perfect for storing:
- Conversation metadata
- Agent responses
- Training parameters
- Performance metrics
- Knowledge base entries

#### Advanced Indexing
- **GIN Indexes**: For fast JSON field queries
- **Full-text Search**: For conversation content and knowledge base
- **Partial Indexes**: For filtered queries on training data

#### Extensions for AI/ML
```sql
-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For similarity search
CREATE EXTENSION IF NOT EXISTS "unaccent"; -- For text normalization
```

### 3. Vector Database Integration (Optional but Recommended)

For advanced semantic search and similarity matching of conversations:

#### Option A: pgvector Extension
```bash
# Install pgvector for PostgreSQL
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

```sql
-- Enable vector extension
CREATE EXTENSION vector;

-- Add vector columns to existing tables
ALTER TABLE conversation_training_data 
ADD COLUMN conversation_embedding vector(1536);  -- OpenAI embedding size

ALTER TABLE agent_knowledge_base 
ADD COLUMN content_embedding vector(1536);
```

#### Option B: Separate Vector Database (Weaviate/Pinecone)
For more advanced vector operations, consider a dedicated vector database:

```python
# Example integration with Weaviate
import weaviate

client = weaviate.Client(
    url="http://localhost:8080",  # Weaviate instance
    auth_client_secret=weaviate.AuthApiKey(api_key="your-api-key"),
)

# Store conversation embeddings
def store_conversation_embedding(conversation_id, text, metadata):
    client.data_object.create(
        data_object={
            "conversation_id": conversation_id,
            "text": text,
            "metadata": metadata
        },
        class_name="ConversationEmbedding"
    )
```

### 4. Recommended Database Schema Optimizations

#### Indexes for Training Data
```sql
-- Conversation training data indexes
CREATE INDEX CONCURRENTLY idx_training_data_category 
ON conversation_training_data(conversation_category);

CREATE INDEX CONCURRENTLY idx_training_data_success_score 
ON conversation_training_data(success_score DESC);

CREATE INDEX CONCURRENTLY idx_training_data_quality 
ON conversation_training_data(is_high_quality, processed_for_training);

-- GIN index for JSON fields
CREATE INDEX CONCURRENTLY idx_training_data_key_phrases 
ON conversation_training_data USING GIN (key_phrases);

CREATE INDEX CONCURRENTLY idx_training_data_user_intents 
ON conversation_training_data USING GIN (user_intents);
```

#### Knowledge Base Indexes
```sql
-- Knowledge base indexes
CREATE INDEX CONCURRENTLY idx_knowledge_base_type_category 
ON agent_knowledge_base(knowledge_type, category);

CREATE INDEX CONCURRENTLY idx_knowledge_base_success_rate 
ON agent_knowledge_base(success_rate DESC);

-- Full-text search
CREATE INDEX CONCURRENTLY idx_knowledge_base_content_fts 
ON agent_knowledge_base USING GIN (to_tsvector('english', content));

-- Trigger phrases similarity search
CREATE INDEX CONCURRENTLY idx_knowledge_base_triggers 
ON agent_knowledge_base USING GIN (trigger_phrases);
```

### 5. Data Partitioning Strategy

For large-scale deployments, consider partitioning training data by date:

```sql
-- Partition training data by month
CREATE TABLE conversation_training_data_2024_01 
PARTITION OF conversation_training_data 
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE conversation_training_data_2024_02 
PARTITION OF conversation_training_data 
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

### 6. Backup and Archival Strategy

```bash
# Automated daily backups
pg_dump -h localhost -U ai_call_user -d ai_call_system \
  --format=custom --compress=5 \
  --file=backup_$(date +%Y%m%d).dump

# Archive old training data (older than 1 year)
# Move to separate archive database or cold storage
```

### 7. Performance Monitoring

```python
# Django settings for query monitoring
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['file'],
        },
    },
}

# Monitor slow queries
DATABASES['default']['OPTIONS']['log_statement'] = 'all'
DATABASES['default']['OPTIONS']['log_min_duration_statement'] = 1000  # Log queries > 1s
```

### 8. Caching Strategy

```python
# Redis for caching frequently accessed data
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Cache knowledge base entries
from django.core.cache import cache

def get_knowledge_by_intent(intent):
    cache_key = f'knowledge_intent_{intent}'
    knowledge = cache.get(cache_key)
    
    if knowledge is None:
        knowledge = AgentKnowledgeBase.objects.filter(
            trigger_phrases__contains=[intent]
        ).order_by('-success_rate')[:10]
        cache.set(cache_key, knowledge, 3600)  # Cache for 1 hour
    
    return knowledge
```

### 9. Scaling Recommendations

#### Read Replicas
```python
# Database routing for read replicas
class DatabaseRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'ai_integration':
            return 'read_replica'
        return 'default'
    
    def db_for_write(self, model, **hints):
        return 'default'
```

#### Connection Pooling
```bash
# Install pgbouncer for connection pooling
sudo apt-get install pgbouncer

# Configure pgbouncer
echo "ai_call_system = host=localhost port=5432 dbname=ai_call_system" >> /etc/pgbouncer/pgbouncer.ini
```

## Implementation Steps

1. **Development Phase**: Continue with SQLite
2. **Staging Environment**: Deploy PostgreSQL with basic configuration
3. **Production Deployment**: 
   - PostgreSQL with full indexing
   - Redis caching
   - Connection pooling
   - Monitoring setup
4. **Scale Phase**: 
   - Add vector database if needed
   - Implement read replicas
   - Set up data partitioning

## Cost Considerations

### PostgreSQL Hosting Options:
- **Self-managed**: $50-200/month (depending on server size)
- **AWS RDS**: $100-500/month (with managed features)
- **Google Cloud SQL**: $80-400/month
- **Azure Database**: $90-450/month

### Vector Database (if needed):
- **Weaviate Cloud**: $25-100/month
- **Pinecone**: $70-500/month
- **Self-hosted Weaviate**: $30-150/month

## Migration Strategy

```python
# Create migration for new training models
python manage.py makemigrations ai_integration

# Custom migration for data conversion if needed
python manage.py makemigrations --empty ai_integration

# In the migration file:
def convert_existing_conversations(apps, schema_editor):
    # Convert existing conversation data to training format
    pass
```

This database architecture will provide:
- ✅ High performance for complex queries
- ✅ Scalability for growing data
- ✅ Advanced search capabilities
- ✅ Efficient storage of JSON data
- ✅ Support for vector operations
- ✅ Production-ready reliability
