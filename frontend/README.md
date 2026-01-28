# Spark Log Analyzer Frontend

Modern React frontend for the Intelligent Apache Spark Log Analyzer.

## Features

- **Dashboard**: Real-time overview of log analysis metrics
- **Upload**: Drag-and-drop log file upload with batch support
- **Log Viewer**: Browse and filter parsed log entries
- **AI Analysis**: Run LLM-powered root cause analysis
- **Reports**: Generate and view analysis reports
- **Settings**: Configure LLM providers and preferences

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Spark Log Analyzer
```

## Tech Stack

- **React 18** - UI framework
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **Lucide React** - Icons
- **Vite** - Build tool
