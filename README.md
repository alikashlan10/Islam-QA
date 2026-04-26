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
