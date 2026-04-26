# Islam-QA — Backend Service

> ⚠️ This project is in early development. Contributions and feedback are welcome.

## Related Repositories

| Service | Repository |
|---|---|
| 🔍 Search Service | [Islam-QA-Search](https://github.com/alikashlan10/Islam-QA-Search) |
| 🖥️ Frontend UI | [Islam-QA-UI](https://github.com/alikashlan10/Islam-QA-UI) |

---

## Overview

Islam-QA Backend is the ingestion and processing engine of the Islam-QA system. It downloads Islamic lecture videos from YouTube, transcribes them, and embeds the transcripts into a vector database for semantic search.

The service is built with Clean Architecture principles — all components are modular and swappable via configuration.

---

## Architecture

```
YouTube Playlist / Video URL
        │
        ▼
    Downloader (yt-dlp)
        │
        ▼
    Transcriber (Groq Whisper)
        │
        ▼
    PostgreSQL (transcripts + metadata)
        │
        ▼
    Embedder (HuggingFace / OpenAI / Cohere / Google)
        │
        ▼
    Vector Store (Qdrant — hybrid dense + sparse search)
```

---

## Features

- YouTube playlist and single video ingestion
- Automatic audio transcription via Groq Whisper
- Hybrid vector search (dense + BM25 sparse) via Qdrant
- Resume capability — skips already processed videos
- Background job processing via Celery + Redis
- Job progress tracking persisted in PostgreSQL
- Fully swappable components via environment config
- FastAPI REST endpoints
- Clean Architecture — domain, application, infrastructure, presentation layers

---

## Tech Stack

| Component | Technology |
|---|---|
| API | FastAPI |
| Task Queue | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Transcription | Groq Whisper |
| Embeddings | LangChain (HuggingFace / OpenAI / Cohere / Google) |
| Vector Store | Qdrant |
| Audio Download | yt-dlp + ffmpeg |

---

## Project Structure

```
src/
├── domain/              # models and enums — no dependencies
├── application/         # use cases, interfaces, factories, mappers
├── infrastructure/      # concrete implementations
│   ├── youtube/         # yt-dlp downloader and playlist fetcher
│   ├── transcribers/    # Groq transcriber
│   ├── persistence/     # ORM models, repositories, database
│   └── celery/          # Celery app and tasks
├── api/                 # FastAPI routers and dependencies
└── scripts/             # utility scripts
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Qdrant (local via Docker or cloud)
- ffmpeg

### Installation

```bash
git clone https://github.com/alikashlan10/Islam-QA
cd Islam-QA
pip install -r requirements.txt
```

### Environment Variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Required variables:

```bash
## logs
LOG_LEVEL = INFO
LOG_FILE = "logs/app.log"

## LLMs
GEMINI_API_KEY="" #but your API key 
GEMINI_MODEL_NAME="gemini-1.5-flash"
GROQ_LLM_MODEL="openai/gpt-oss-120b"

## transcriber provider
TRANSCRIBER_PROVIDER = "groq" #(localwhisper,whisperapi,groq,assemblyai)
GROQ_API_KEY = "" # your groq API key 
GROQ_WHISPER_MDOEL = "whisper-large-v3"

## Database
DATABASE_URL = "" # your database connection string (URL)

# App
CHUNKING_STRATEGY=recursive
VECTOR_STORE_PROVIDER = qdrant
EMBEDDING_PROVIDER = huggingface
EMBEDDING_MODEL_NAME = "embed-multilingual-v3.0"
COHERE_API_KEY = ""
CHUNK_SIZE=500
CHUNK_OVERLAP=100
AUDIO_OUTPUT_DIR = "./video_downloads"
QA_EXTRACTOR_PROVIDER = "gemini"

##Vectordb
QDRANT_URL = "" # your qdrant url
QDRANT_API_KEY = "" you cohere API key
QDRANT_COLLECTION_NAME = islam_qa_v1
QDRANT_VECTOR_SIZE = 1024


##Emebdding model
HUGGINGFACE_EMBEDDING_MODEL_NAME = ""


##redis
REDIS_URL= "redis://localhost:6379/0"
```

### Database Setup

```bash
alembic upgrade head
```


### Start Redis (Docker)

```bash
docker run -d --name islam-qa-redis -p 6379:6379 redis:7
```

### Run the API

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Run the Celery Worker

```bash
celery -A src.infrastructure.celery.celery_app worker --loglevel=info
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/ingest/playlist` | Ingest a YouTube playlist |
| POST | `/embed` | Embed all unembedded transcripts |
| GET | `/jobs/{job_id}` | Get job status and progress |
| GET | `/health` | Health check |


---

## License

MIT
