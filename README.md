# Life State Simulation

A complete actor-based life modeling system with FastAPI backend and React dashboard for real-time monitoring.

## Overview

Life State is a sophisticated simulation framework that models the daily lives of virtual actors with realistic behaviors, resource management, and time-based scheduling. The system includes:

- **FastAPI Backend**: REST API and WebSocket server for simulation control
- **React Dashboard**: Professional real-time monitoring interface
- **Simulation Engine**: Advanced actor behavior and world state management
- **Time Management**: Multi-world forking and time-jump capabilities

## Architecture

```
life_state/
├── api.py                 # FastAPI application with REST + WebSocket endpoints
├── ws_manager.py          # WebSocket connection management
├── simulator.py           # Core simulation engine
├── models.py              # Pydantic data models
├── world.py               # World initialization and management
├── states.py              # Actor state definitions
├── actions.py             # Actor action system
├── probability.py         # Probability-based decision making
├── time_jump.py           # Multi-world time-jump system
├── calendar_scheduler.py  # Actor scheduling system
├── tick_engine.py         # Simulation tick processing
├── io_utils.py            # File I/O utilities
└── tests/                 # Comprehensive test suite

ui/                        # React + Tailwind dashboard
├── src/
│   ├── components/        # React components
│   ├── hooks/             # Custom hooks (WebSocket, etc.)
│   ├── types.ts           # TypeScript definitions
│   └── App.tsx            # Main application
├── tailwind.config.js     # Tailwind configuration
└── vite.config.ts         # Vite build configuration
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn

### 1. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn life_state.api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

### 3. Full Development Workflow

For complete development with live simulation:

```bash
# Terminal 1: Start simulation with live mode
python -m life_state.simulator --minutes 1440 --live

# Terminal 2: Start FastAPI server
uvicorn life_state.api:app --reload

# Terminal 3: Start React development server
cd ui && npm run dev
```

## API Endpoints

### REST API

- `GET /api/worlds` - List all available worlds
- `GET /api/worlds/{world_id}/tick/{tick_n}` - Get world state at specific tick
- `POST /api/worlds/{world_id}/start` - Start simulation for world
- `POST /api/worlds/{world_id}/stop` - Stop simulation for world
- `GET /api/health` - Health check endpoint

### WebSocket

- `WS /ws/worlds/{world_id}` - Real-time world state updates

### Example API Usage

```python
import requests

# Get available worlds
worlds = requests.get("http://localhost:8000/api/worlds").json()
print(f"Available worlds: {worlds}")

# Get current world state
world_id = "main"
tick_data = requests.get(f"http://localhost:8000/api/worlds/{world_id}/tick/0").json()
print(f"Actors: {len(tick_data['actors'])}")
print(f"Average hunger: {tick_data['world_stats']['avg_hunger']}")

# Start simulation
response = requests.post(f"http://localhost:8000/api/worlds/{world_id}/start")
print(f"Simulation started: {response.json()}")
```

## Dashboard Features

### Real-time Actor Dashboard

- **Live Table**: 20 actors with real-time state updates
- **Resource Monitoring**: Hunger, fatigue, and mood tracking
- **State Visualization**: Color-coded actor states
- **Responsive Design**: Desktop table, mobile cards

### World Statistics Panel

- **Radial Charts**: Interactive progress gauges using Recharts
- **Population Metrics**: Average hunger, fatigue, mood levels
- **Activity Counters**: Sleeping actors, active worlds
- **Health Summary**: Population-wide resource tracking

### Navigation & Controls

- **Collapsible Sidebar**: World selection and navigation
- **Connection Status**: Real-time WebSocket connection indicator
- **Simulation Controls**: Start/stop/reset simulation
- **Clock Display**: Current simulation time and tick counter

## Configuration

### Backend Configuration

The simulation can be configured via `life_state/world.py`:

```python
config = {
    'fatigue_rate': {
        'sleeping': -5.0,
        'idle': 0.2,
        'focused_work': 3.0,
        # ... other states
    },
    'hunger_rate': {
        'eating': -15.0,
        'idle': 0.8,
        # ... other states
    },
    'mood_modifiers': {
        'sleeping': 0.1,
        'eating': 0.15,
        # ... other states
    }
}
```

### Frontend Configuration

Customize the dashboard via `ui/tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          500: '#0ea5e9',
          600: '#0284c7',
          // ... custom colors
        }
      }
    }
  }
}
```

## Testing

### Backend Tests

```bash
# Run all Python tests
pytest life_state/tests/

# Run with coverage
pytest --cov=life_state life_state/tests/

# Run specific test file
pytest life_state/tests/test_api.py -v
```

### Frontend Tests

```bash
cd ui

# Run React tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test
npm test -- useWebSocket.test.ts
```

## Production Deployment

### Backend Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn life_state.api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend Deployment

```bash
cd ui

# Build for production
npm run build

# Serve static files (FastAPI will serve from ui/dist/)
# Or deploy to CDN/static hosting
```

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY life_state/ life_state/
COPY ui/dist/ ui/dist/

EXPOSE 8000
CMD ["uvicorn", "life_state.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Performance & Security

### Performance Optimizations

- **WebSocket Connection Pooling**: Efficient real-time updates
- **Bundle Optimization**: React app < 200KB uncompressed
- **Tree Shaking**: Optimized icon and chart libraries
- **Caching**: API response caching for static data

### Security Features

- **CORS Configuration**: Secure cross-origin requests
- **Input Validation**: Pydantic model validation
- **WebSocket Security**: Connection authentication and rate limiting
- **Static File Serving**: Secure static asset delivery

## Development Guidelines

### Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Strict mode enabled, explicit types
- **React**: Functional components with hooks
- **CSS**: Tailwind utility classes, custom components

### Git Workflow

```bash
# Feature development
git checkout -b feature/new-dashboard-component
git commit -m "feat: add real-time actor status component"
git push origin feature/new-dashboard-component

# Create pull request for review
```

### Testing Requirements

- **Backend**: >90% test coverage for API endpoints
- **Frontend**: Unit tests for hooks and components
- **Integration**: End-to-end WebSocket functionality
- **Performance**: Bundle size and load time monitoring

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check FastAPI server is running on port 8000
   - Verify CORS settings in `api.py`
   - Check browser console for connection errors

2. **React Build Errors**
   - Ensure Node.js 18+ is installed
   - Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
   - Check for TypeScript errors: `npm run build`

3. **API 404 Errors**
   - Verify FastAPI server is running
   - Check API endpoint URLs in frontend code
   - Review proxy configuration in `vite.config.ts`

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn life_state.api:app --reload --log-level debug

# React development with verbose logging
npm run dev -- --debug
```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Add comprehensive tests**
4. **Update documentation**
5. **Submit a pull request**

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/life_state.git
cd life_state

# Setup Python environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Setup Node.js environment
cd ui
npm install
cd ..

# Run development servers
make dev  # or follow manual steps above
```

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@lifestate.dev