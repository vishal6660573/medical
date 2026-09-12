# SmartHealth — Intelligent Healthcare & Disease Prediction Platform

SmartHealth is a full-stack healthcare platform featuring automated disease prediction (Diabetes, Heart Disease, Chest X-ray analysis), medical report OCR parsing, patient records management, doctor consultations, and an AI-powered medical assistant powered by Ollama (Local LLM).

---

## 🏛️ System Architecture

Docker is used **ONLY** for running the PostgreSQL 16 database. The FastAPI backend and React (Vite) frontend run directly on the host machine.

```
                                  +-------------------------------------------------------+
                                  |                     End Users                         |
                                  |           (Patients, Doctors, Administrators)         |
                                  +---------------------------+---------------------------+
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |               React Frontend (Vite SPA)               |
                                  |                 http://localhost:5173                 |
                                  +---------------------------+---------------------------+
                                                              |
                                                   HTTP / API Requests (/api/*)
                                                              |
                                                              v
      +---------------------------------------------------------------------------------------------------------------+
      |                                      FastAPI Backend (Local Host)                                             |
      |                                         http://localhost:8000                                                 |
      |                                                                                                               |
      |   +---------------------+   +---------------------+   +---------------------+   +-------------------------+   |
      |   |  JWT Authentication |   | Patient Management  |   | Medical Report OCR  |   |    Ollama Local LLM     |   |
      |   |   & Role Access     |   |   & Doctor Visits   |   | (EasyOCR + Poppler) |   |        (MediBot)        |   |
      |   +---------------------+   +---------------------+   +---------------------+   +-------------------------+   |
      |                                                                                                               |
      |   +-------------------------------------------------------------------------------------------------------+   |
      |   |                                          Machine Learning Models                                      |   |
      |   |   - Diabetes Risk: Logistic Regression + StandardScaler                                               |   |
      |   |   - Heart Disease: Random Forest Classifier                                                           |   |
      |   |   - Chest X-Ray: DenseNet121 Deep Learning CNN (TensorFlow / Keras)                                   |   |
      |   +-------------------------------------------------------------------------------------------------------+   |
      +-------------------------------------------------------+-------------------------------------------------------+
                                                              |
                                                 SQLAlchemy ORM (Port 5432)
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |             PostgreSQL 16 (Docker Container)          |
                                  |           Container: smarthealth-postgres             |
                                  |               Port: localhost:5432                    |
                                  |            Persistent Volume: postgres_data           |
                                  +-------------------------------------------------------+
```

---

## 💻 Technology Stack

* **Frontend:** React 18, Vite, React Router v6, Tailwind / Custom Modern CSS, Axios, Lucide Icons
* **Backend:** Python 3.10+, FastAPI, Uvicorn, Pydantic v2
* **Database:** PostgreSQL 16 (Dockerized), SQLAlchemy 2.0, Alembic, psycopg2-binary
* **Machine Learning & Deep Learning:**
  * **Diabetes:** Logistic Regression with `StandardScaler`
  * **Heart Disease:** Random Forest Classifier
  * **Chest X-ray:** DenseNet121 CNN with TensorFlow / Keras
  * **Medical Report OCR:** EasyOCR, Poppler, OpenCV, Pillow
* **AI Chatbot:** Ollama Local LLM via `httpx`
* **Containerization:** Docker & Docker Compose (PostgreSQL only)

---

## 📁 Project Directory Structure

```text
smarthealth-main/
├── backend/
│   ├── alembic/                 # Database migrations
│   ├── alembic.ini              # Alembic configuration
│   ├── app/
│   │   ├── api/routes/          # FastAPI routes (auth, patients, health, chatbot, admin)
│   │   ├── auth/                # JWT handler, password hashing (bcrypt), dependencies
│   │   ├── core/                # Configuration, logging, exception handlers
│   │   ├── database/            # SQLAlchemy database engine and models
│   │   └── ocr/                 # EasyOCR engine and report parser
│   ├── models/                  # Trained ML models and weights (diabetes, heart, xray)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Prediction services and storage handlers
│   ├── requirements.txt         # Backend Python dependencies
│   ├── .env.example             # Backend environment template
│   └── venv/                    # Python virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components (Sidebar, ChatbotWidget, PrivateRoute)
│   │   ├── context/             # AuthContext state provider
│   │   ├── pages/               # Dashboards, predictions, login, register, admin
│   │   ├── services/            # Axios API client
│   │   ├── App.jsx              # Routing and layouts
│   │   └── main.jsx             # React DOM entry point
│   ├── package.json             # Frontend dependencies and scripts
│   └── vite.config.js           # Vite configuration & dev proxy
│
├── docker-compose.yml           # PostgreSQL Docker service
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore specifications
└── README.md                    # Project documentation
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/smarthealth` |
| `POSTGRES_DB` | PostgreSQL database name | `smarthealth` |
| `POSTGRES_USER` | PostgreSQL superuser | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | `super-secret-healthcare-key-change-in-production` |
| `OLLAMA_BASE_URL` | Ollama Host URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama Model Name | `llama3.2` |

---

## 🚀 Quick Start Guide

### Step 1: Start PostgreSQL (Docker)

Start the PostgreSQL database container in detached mode:

```bash
docker compose up -d
```

Check running containers (only `smarthealth-postgres` should be running):

```bash
docker ps
```

To stop PostgreSQL when needed:

```bash
docker compose down
```

---

### Step 2: Start Backend (FastAPI on Host)

In a terminal:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

* **Backend Base URL:** [http://localhost:8000](http://localhost:8000)
* **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Step 3: Start Frontend (React / Vite on Host)

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

* **Frontend Application:** [http://localhost:5173](http://localhost:5173)

---

## 🔒 Security & Persistence

1. **Database Persistence:** PostgreSQL data is stored in the Docker named volume `postgres_data` and persists across container restarts.
2. **Localhost Binding:** PostgreSQL is exposed on `localhost:5432`.
3. **CORS Security:** The FastAPI backend is configured to accept requests exclusively from the local frontend origins (`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`).
