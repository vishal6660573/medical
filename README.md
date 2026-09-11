# SmartHealth — Intelligent Healthcare & Disease Prediction Platform

SmartHealth is a production-ready, full-stack healthcare platform featuring automated disease prediction (Diabetes, Heart Disease, Chest X-ray analysis), medical report OCR parsing, patient records management, doctor consultations, and an AI-powered medical assistant powered by Google Gemini.

---

## 🏛️ System Architecture

### Application Architecture

```
                                  +-------------------------------------------------------+
                                  |                     End Users                         |
                                  |           (Patients, Doctors, Administrators)         |
                                  +---------------------------+---------------------------+
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |                     Web Browser                       |
                                  |              (React 18 + Vite Frontend SPA)           |
                                  +---------------------------+---------------------------+
                                                              |
                                                   HTTP / API Requests (/api/*)
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |                   Nginx Reverse Proxy                 |
                                  |                 (Port 80 / Reverse Proxy)             |
                                  +---------------------------+---------------------------+
                                                              |
                                                   Proxy Pass to Backend (Port 8000)
                                                              |
                                                              v
      +---------------------------------------------------------------------------------------------------------------+
      |                                           FastAPI Backend Service                                             |
      |                                                                                                               |
      |   +---------------------+   +---------------------+   +---------------------+   +-------------------------+   |
      |   |  JWT Authentication |   | Patient Management  |   | Medical Report OCR  |   |   Google Gemini Chat    |   |
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
                                                        SQLAlchemy ORM
                                                              |
                                                              v
                                  +-------------------------------------------------------+
                                  |                 PostgreSQL 16 Database                |
                                  |            (Persistent Storage: Docker Volumes)        |
                                  |                                                       |
                                  |  - users                 - doctors                    |
                                  |  - patients              - visits                     |
                                  |  - medications           - prediction_results         |
                                  +-------------------------------------------------------+
```

---

## 💻 Technology Stack

* **Frontend:** React 18, Vite, React Router v6, Tailwind / Custom Modern CSS, Axios, Lucide Icons
* **Backend:** Python 3.10, FastAPI, Uvicorn, Pydantic v2
* **Database & ORM:** PostgreSQL 16, SQLAlchemy 2.0, Alembic, psycopg2-binary
* **Machine Learning & Deep Learning:**
  * **Diabetes:** Logistic Regression with `StandardScaler`
  * **Heart Disease:** Random Forest Classifier
  * **Chest X-ray:** DenseNet121 CNN with TensorFlow / Keras 2.15
  * **Medical Report OCR:** EasyOCR, Poppler, OpenCV, Pillow
* **AI Chatbot:** Google Gemini (`gemini-2.0-flash`) via `google-generativeai`
* **DevOps & Containerization:** Docker, Docker Compose, Nginx

---

## 📁 Project Directory Structure

```text
smarthealth-main/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI routes (auth, patients, health, chatbot, admin)
│   │   ├── auth/                # JWT handler, password hashing (bcrypt), dependencies
│   │   ├── core/                # Configuration, logging, exception handlers
│   │   ├── database/            # SQLAlchemy database engine and models
│   │   └── ocr/                 # EasyOCR engine and report parser
│   ├── models/                  # Trained ML models and weights (diabetes, heart, xray)
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── services/                # Prediction services and storage handlers
│   ├── alembic/                 # Database migrations
│   ├── alembic.ini              # Alembic configuration
│   ├── requirements.txt         # Backend Python dependencies
│   └── Dockerfile               # Backend Docker container specification
│
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components (Sidebar, ChatbotWidget, PrivateRoute)
│   │   ├── context/             # AuthContext state provider
│   │   ├── pages/               # Dashboards, predictions, login, register, admin
│   │   ├── services/            # Axios API client
│   │   ├── App.jsx              # Routing and layouts
│   │   └── main.jsx             # React DOM entry point
│   ├── nginx.conf               # Production Nginx reverse proxy configuration
│   ├── package.json             # Frontend dependencies and scripts
│   ├── vite.config.js           # Vite configuration & dev proxy
│   └── Dockerfile               # Multi-stage frontend Docker build
│
├── docker-compose.yml           # Multi-container Docker Compose setup
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore specifications
├── .dockerignore                # Docker ignore specifications
└── README.md                    # Project documentation
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` and fill in your configuration:

```bash
cp .env.example .env
```

Key variables:

| Variable | Description | Default / Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://postgres:postgres@localhost:5432/smarthealth` |
| `JWT_SECRET_KEY` | Secret key for signing JWT tokens | `super-secret-healthcare-key-change-in-production` |
| `GEMINI_API_KEY` | Google Gemini API Key | `AIzaSy...` |
| `POSTGRES_USER` | PostgreSQL superuser | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `postgres` |
| `POSTGRES_DB` | PostgreSQL database name | `smarthealth` |

---

## 🐳 Docker Compose Deployment (Recommended)

Docker Compose manages the complete multi-container stack: **Frontend**, **Backend**, and **PostgreSQL**.

### 1. Build and Start All Services

Run the following command in the root directory:

```bash
docker compose up --build
```

To run in detached (background) mode:

```bash
docker compose up --build -d
```

### 2. Service Endpoints

Once running, the services are available at:

* **Frontend Web Application:** [http://localhost](http://localhost) (Port 80)
* **Backend API / Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
* **PostgreSQL Database:** `localhost:5432`

### 3. Manage Docker Services

```bash
# Check status of running containers
docker compose ps

# View real-time logs for all services
docker compose logs -f

# View logs for a specific service (frontend, backend, or db)
docker compose logs -f backend

# Stop all containers
docker compose stop

# Stop and remove all containers, networks, and volumes
docker compose down

# Stop and remove containers including data volumes (fresh start)
docker compose down -v
```

---

## 🛠️ Local Development Setup (Without Docker)

### 1. Prerequisites
* Python 3.10
* Node.js 18+ and npm
* PostgreSQL 16 (running locally on port 5432)

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (optional, or tables auto-create on startup)
alembic upgrade head

# Start FastAPI server with live reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend interactive API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Frontend Setup

```bash
# In a new terminal, navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite development server
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔒 Security & Persistence Best Practices

1. **Secrets Isolation:** Sensitive variables (JWT secret, DB credentials, Gemini API key) are stored in `.env` and not tracked in Git.
2. **Network Segregation:** PostgreSQL and backend communicate securely over the internal Docker network `smarthealth-network`.
3. **Persistent Storage:** Database records persist across container restarts via the named Docker volume `postgres_data`.
4. **Health Checks:** Container health checks ensure dependent services only start when the database is fully ready.
