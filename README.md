# Moment Finder AI Backend

Moment Finder AI is a specialized video analysis tool designed to help content creators, media analysts, and video essayists instantly locate specific moments within large video files.

Instead of manually scrubbing through hours of footage, users can upload videos, select a character, and semantically search for scenes (e.g., "Rick drinking from his flask", "Thanos snapping"). This backend service provides the foundational API, storage management, and background processing pipeline necessary to perform complex, long-running AI video analysis tasks.

## 🏗️ Architecture Design

This project follows a **Service Layer Architecture** (inspired by Clean/Hexagonal Architecture). This ensures that business logic is completely isolated from the web framework, databases, and third-party APIs.

### Backend Structure

```text
moment-finder-ai-backend/
├── app/
│   ├── api/             # 1. Presentation Layer (FastAPI Routers & Endpoints)
│   ├── services/        # 2. Business Logic Layer (Core application logic)
│   ├── db/              # 3. Data Access Layer / Repositories (Database interactions)
│   ├── schemas/         # 4. Data Validation (Pydantic Models for requests/responses)
│   ├── models/          # 5. Database Entities (SQLAlchemy ORM Models)
│   ├── core/            # 6. Configuration & Security (Settings, environment vars)
│   └── main.py          # FastAPI application entrypoint
├── tests/               # Unit and Integration Tests
├── requirements.txt     # Project dependencies
└── README.md            # You are here
```

## 📦 Tech Stack & Package Explanations

This section breaks down exactly what each library in `requirements.txt` does and *why* it was chosen for this project.

### Core Framework
* **`fastapi`**: The core web framework used to build our API. It is renowned for being incredibly fast (on par with NodeJS and Go), asynchronous out of the box (vital for handling video uploads without blocking), and it automatically generates interactive API documentation.
* **`uvicorn[standard]`**: FastAPI is just the framework. Uvicorn is the actual ASGI *web server* that runs the FastAPI application and listens for HTTP requests on a specific port.

### Data Validation & Configuration
* **`pydantic`**: Used by FastAPI to define data schemas. When a user sends a JSON request to the API, Pydantic ensures the data matches the expected format (e.g., confirming a field is an integer and not a string) before it ever touches our business logic.
* **`pydantic-settings`**: Manages environment variables and configuration (like database passwords and API keys). It enforces type checking on our configurations so the app won't even start if a mandatory environment variable is missing.

### Database Operations (SQL)
* **`sqlalchemy`**: A powerful Object Relational Mapper (ORM). Instead of writing raw SQL commands (like `SELECT * FROM users`), we interact with the database using standard Python classes out of the `models/` directory.
* **`alembic`**: A lightweight database migration tool specifically used alongside SQLAlchemy. If we decide to add a new column to a database table next week, Alembic writes the migration script to update the live database safely without wiping our data.
* **`psycopg2-binary`**: The underlying PostgreSQL driver for Python. When SQLAlchemy needs to talk directly to the PostgreSQL database engine, it uses this C-based adapter.

### Video Storage (Phase 2)
Video files are massive, so we do not store them in the PostgreSQL database. Instead, we use "Object Storage" (Amazon S3). For local development, we use **MinIO**, which is a free, open-source clone of Amazon S3 that runs on your laptop and intercepts S3 commands.
* **`boto3`**: The official Amazon Web Services (AWS) SDK for Python. We use this to write the S3 upload code. By pointing it to MinIO locally, we can develop and test our S3 logic for free, and then seamlessly switch to real AWS S3 in production with zero code changes.


### Background Task Processing
Since video analysis takes a long time, we cannot make the user wait for an HTTP response. We use an asynchronous worker pipeline.
* **`celery`**: A distributed task queue. When the API receives a video, it immediately responds "Video processing started." It then hands off the actual processing job to a separate Celery Python process running in the background.
* **`redis`**: An in-memory key-value store. Celery uses Redis as its "message broker." The API places a message in Redis, and the Celery worker checks Redis to see if there is pending work.

### Networking & Testing
* **`httpx`**: A fully featured HTTP client for Python. This allows our backend to make requests to other external APIs (such as sending data to an external AI model like Gemini).
* **`pytest`**: The framework we use to write automated unit and integration tests to ensure our API and business logic handlers are functioning correctly.
* **`python-dotenv`**: Used in local development to load environment variables from a `.env` file into our Python runtime.
* **`python-multipart`**: A library required by FastAPI specifically to handle and stream file uploads (like pushing `.mp4` files from the client to the server).

## 🚀 Local Setup & Development

### Prerequisites
- Python 3.10+ (Currently using Python 3.13)
- PostgreSQL (or Docker to run Postgres locally)
- Redis (or Docker to run Redis locally)
- MinIO (Standalone executable to emulate Amazon S3 locally for video uploads)


### 1. Set up the Environment
Clone the repository and spin up a virtual environment.

```bash
# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate
# Activate it (Mac/Linux)
# source venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
*(Note: A `.env.example` file will be created shortly. Copy it to `.env` and fill in your local Postgres and Redis credentials).*

### 3. Running the Server

To start the FastAPI server locally in development mode, you have two options:

**Option A: The Modern FastAPI CLI (Recommended for Development)**
```bash
fastapi dev app/main.py
```
*This is the newer, official command introduced in FastAPI v0.111.0. It automatically enables hot-reloading and provides a cleaner development output.*

**Option B: The Traditional Uvicorn Command (Industry Standard)**
```bash
uvicorn app.main:app --reload
```
*Uvicorn is the actual ASGI web server that powers FastAPI under the hood. While `fastapi dev` is a wrapper around Uvicorn, learning the Uvicorn command is crucial because it is how you will run the application in Production (without the `--reload` flag).*

*   The API will be running at `http://127.0.0.1:8000`
*   **API Documentation**: You can view the automatically generated interactive documentation (Swagger UI) by navigating to `http://127.0.0.1:8000/docs` in your browser.
