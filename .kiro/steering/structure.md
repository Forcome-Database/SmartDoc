# Project Structure

## Architecture

Frontend-backend separation with microservices architecture using Docker Compose orchestration.

## Directory Layout

```
enterprise-idp-platform/
├── backend/                    # Python/FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── v1/
│   │   │       └── endpoints/ # Feature endpoints (auth, upload, tasks, rules, audit, webhook, dashboard, users, system)
│   │   ├── core/              # Core configuration (config, security, dependencies)
│   │   ├── models/            # SQLAlchemy database models
│   │   ├── schemas/           # Pydantic validation schemas
│   │   ├── services/          # Business logic (OCR, file processing, extraction, validation)
│   │   └── tasks/             # Async task workers (OCR worker, push worker)
│   ├── alembic/               # Database migration scripts
│   ├── scripts/               # Utility scripts (init.sql)
│   ├── main.py                # Application entry point
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Backend container image
│
├── frontend/                   # Vue 3 frontend
│   ├── src/
│   │   ├── api/               # Backend API wrappers
│   │   ├── components/        # Reusable UI components
│   │   ├── views/             # Page components (Dashboard, Rules, Tasks, Audit, Webhooks, System)
│   │   ├── router/            # Vue Router configuration
│   │   ├── stores/            # Pinia state management
│   │   └── utils/             # Utility functions
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.js         # Vite build configuration
│   ├── tailwind.config.js     # Tailwind CSS configuration
│   ├── postcss.config.js      # PostCSS configuration
│   ├── nginx.conf             # Nginx web server configuration
│   └── Dockerfile             # Frontend container image
│
├── .kiro/                      # Kiro IDE configuration
│   ├── specs/                 # Feature specifications
│   └── steering/              # AI assistant guidance (this directory)
│
├── docker-compose.yml          # Production service orchestration
├── docker-compose.dev.yml      # Development overrides (hot reload)
├── .env.example               # Environment variables template
├── .gitignore
├── README.md                  # Main documentation
├── Prd.md                     # Product requirements (Chinese)
├── TechnologyStack.md         # Tech stack details
└── DirectoryStructure.md      # Structure documentation
```

## Key Conventions

### Backend Structure

- **API Versioning**: All endpoints under `/api/v1/`
- **Module Organization**: Feature-based modules in `app/api/v1/endpoints/`
- **Models**: SQLAlchemy models in `app/models/`, one file per entity
- **Schemas**: Pydantic schemas in `app/schemas/`, separate request/response models
- **Services**: Business logic in `app/services/`, stateless service classes
- **Tasks**: Async workers in `app/tasks/` for OCR processing and webhook delivery

### Frontend Structure

- **Component Naming**: PascalCase for components (e.g., `TaskList.vue`)
- **View Organization**: One view per route in `src/views/`
- **API Layer**: Centralized API calls in `src/api/`, organized by feature
- **State Management**: Pinia stores in `src/stores/`, one store per domain
- **Routing**: Lazy-loaded routes in `src/router/index.js`

### Code Style

- **Backend**: Follow PEP 8, use type hints, async/await for I/O operations
- **Frontend**: Vue 3 Composition API, `<script setup>` syntax preferred
- **Naming**: 
  - Python: snake_case for functions/variables, PascalCase for classes
  - JavaScript: camelCase for functions/variables, PascalCase for components
- **Documentation**: Docstrings for Python functions, JSDoc for complex JS functions

### Configuration

- **Environment Variables**: Use `.env` file, never commit secrets
- **Database**: Connection pooling via SQLAlchemy, migrations via Alembic
- **CORS**: Configured in `main.py` for development and production origins
- **API Documentation**: Auto-generated via FastAPI at `/api/docs`

### Docker

- **Multi-stage Builds**: Optimize image size
- **Health Checks**: All services have health check configurations
- **Volume Mounts**: Development mode mounts source code for hot reload
- **Service Dependencies**: Use `depends_on` with health conditions
