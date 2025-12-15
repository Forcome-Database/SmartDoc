# Enterprise IDP Platform - Frontend

Vue 3 + Vite frontend application for the Enterprise IDP Platform.

## Tech Stack

- **Framework**: Vue 3.5 (Composition API with `<script setup>`)
- **Build Tool**: Vite 5
- **UI Library**: Ant Design Vue 4.2
- **State Management**: Pinia
- **Styling**: Tailwind CSS 3.4
- **HTTP Client**: Axios
- **Charts**: ECharts 5 with vue-echarts
- **Date Handling**: Day.js

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API modules
│   │   ├── auth.js       # Authentication API
│   │   ├── task.js       # Task management API
│   │   ├── rule.js       # Rule management API
│   │   ├── dashboard.js  # Dashboard API
│   │   ├── request.js    # Axios instance with interceptors
│   │   └── index.js      # API exports
│   ├── components/       # Reusable components
│   │   └── Layout/       # Layout components
│   │       └── MainLayout.vue
│   ├── views/            # Page components
│   │   └── Login.vue     # Login page
│   ├── router/           # Vue Router configuration
│   │   └── index.js      # Route definitions
│   ├── stores/           # Pinia stores
│   │   ├── authStore.js  # Authentication state
│   │   └── index.js      # Store exports
│   ├── utils/            # Utility functions
│   │   ├── constants.js  # Constants and enums
│   │   ├── format.js     # Formatting utilities
│   │   └── index.js      # Utility exports
│   ├── App.vue           # Root component
│   ├── main.js           # Application entry point
│   └── style.css         # Global styles with Tailwind
├── public/               # Static assets
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # Tailwind CSS configuration
├── postcss.config.js     # PostCSS configuration
├── package.json          # Dependencies
├── .env.example          # Environment variables template
└── Dockerfile            # Production container image

## Development

### Prerequisites

- Node.js 18+ and npm

### Install Dependencies

```bash
npm install
```

### Development Server

```bash
npm run dev
```

The application will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Lint Code

```bash
npm run lint
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
# API Configuration
VITE_API_BASE_URL=/api
VITE_API_TARGET=http://localhost:8000

# Application Configuration
VITE_APP_TITLE=Enterprise IDP Platform
VITE_APP_VERSION=1.0.0
```

## API Proxy Configuration

The Vite dev server is configured to proxy API requests to the backend:

- `/api/*` → `http://localhost:8000/api/*` (or `VITE_API_TARGET`)

This allows the frontend to make API calls without CORS issues during development.

## Code Style

- Use Vue 3 Composition API with `<script setup>` syntax
- Use camelCase for JavaScript variables and functions
- Use PascalCase for Vue components
- Use kebab-case for component file names in templates
- Follow Vue 3 style guide: https://vuejs.org/style-guide/

## Key Features Implemented

### Authentication
- Login page with form validation
- JWT token management
- Auth store with Pinia
- Route guards for protected pages

### API Layer
- Centralized Axios instance with interceptors
- Request/response interceptors for token injection and error handling
- Modular API organization by feature

### Utilities
- Constants for task status, user roles, etc.
- Formatting functions for dates, file sizes, numbers, etc.
- Confidence level helpers

### Layout
- Main layout with header, sidebar, and content area
- Responsive design
- User dropdown menu
- Navigation menu

## Next Steps

The following components need to be implemented:

1. **Dashboard** - Metrics cards, charts, and statistics
2. **Rule Management** - Rule list, editor, version control, sandbox testing
3. **Task Management** - Task list, detail view, status tracking
4. **Audit Workbench** - PDF preview, OCR highlighting, data correction
5. **Webhook Configuration** - Webhook CRUD, connectivity testing
6. **System Settings** - User management, system configuration

## Docker Deployment

### Build Image

```bash
docker build -t idp-frontend .
```

### Run Container

```bash
docker run -p 80:80 idp-frontend
```

The application will be served by Nginx and available at http://localhost

## Notes

- The frontend uses Ant Design Vue's default theme with custom Tailwind colors
- Tailwind's preflight is disabled to avoid conflicts with Ant Design
- All API calls go through the centralized request instance for consistent error handling
- Authentication state is persisted in localStorage
