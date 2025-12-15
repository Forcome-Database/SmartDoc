# Technology Stack

## Backend

- **Language**: Python 3.11+
- **Framework**: FastAPI 0.109+ (async web framework)
- **Database**: MySQL 8.0 with SQLAlchemy 2.0 ORM
- **Migration**: Alembic for database version control
- **Cache**: Redis 7
- **Message Queue**: RabbitMQ 3.12
- **Object Storage**: MinIO (S3-compatible)
- **OCR Engines**: PaddleOCR 3.3, Tesseract 5.5, UmiOCR (Docker HTTP 服务)
- **PDF Processing**: pdfplumber, PyMuPDF, pdf2image
- **LLM Integration**: Agently 4.0
- **Security**: python-jose, passlib, bcrypt
- **Validation**: Pydantic 2.5+
- **Logging**: loguru

### Important: Documentation Lookup

Before implementing features using PaddleOCR, Tesseract, or Agently, **always use Context7 or web scraping tools** to check the latest API usage and best practices for these specific versions:
- PaddleOCR 3.3: Check official docs for API changes
- Tesseract 5.5: Verify command-line options and language support
- Agently 4.0: Review workflow patterns and agent configuration

## Frontend

- **Framework**: Vue 3.5 (Composition API)
- **Build Tool**: Vite 5
- **UI Library**: Ant Design Vue 4.2
- **State Management**: Pinia
- **Styling**: Tailwind CSS 3.4
- **HTTP Client**: Axios
- **Charts**: ECharts 5 with vue-echarts

## Infrastructure

- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (static files and reverse proxy)
- **Development**: Hot reload support via docker-compose.dev.yml

## Common Commands

### Development

```bash
# Start all services (development mode with hot reload)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Start production mode
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Run tests
pytest
```

### Frontend

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint and fix
npm run lint
```

### Docker Operations

```bash
# Rebuild specific service
docker-compose build backend
docker-compose up -d backend

# Execute commands in container
docker-compose exec backend alembic upgrade head
docker-compose exec mysql mysql -u root -p

# View service status
docker-compose ps
```

## API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json

## Service Ports

- Frontend: http://localhost (port 80)
- Backend API: http://localhost:8000
- MySQL: localhost:3306
- Redis: localhost:6379
- RabbitMQ: localhost:5672 (AMQP), localhost:15672 (Management UI)
- MinIO: localhost:9000 (API), localhost:9001 (Console)
