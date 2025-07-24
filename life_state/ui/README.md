# Life State Simulation Frontend

**TODO: Prompt 3** - This directory will contain a React/Tailwind CSS frontend for the life_state simulation.

## Planned Features

### Core Components
- **WorldView**: Main dashboard showing world state overview
- **ActorList**: List of all actors with current states and resources
- **LocationMap**: Visual representation of locations and actor positions
- **TimeControls**: Play/pause/step controls for simulation
- **ActorDetail**: Detailed view of individual actor state and history

### Real-time Features
- **Live Updates**: WebSocket connection for real-time state updates
- **State Visualization**: Charts and graphs showing resource changes over time
- **Event Log**: Real-time feed of actor actions and state changes
- **Timeline View**: Visual timeline of world events

### Time-Jump Features
- **Fork Visualization**: Tree view of world forks and timelines
- **Timeline Comparison**: Side-by-side comparison of different world states
- **Jump Controls**: Interface for triggering time-jumps
- **Divergence Metrics**: Visual indicators of timeline differences

### Configuration
- **World Settings**: Interface for configuring simulation parameters
- **Actor Creation**: Forms for creating and editing actors
- **Schedule Editor**: Calendar interface for actor scheduling
- **Probability Tuning**: Sliders and controls for probability weights

## Technology Stack

- **React 18+**: Modern React with hooks and concurrent features
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Chart.js/D3.js**: Data visualization for metrics and timelines
- **React Query**: Data fetching and caching
- **WebSocket**: Real-time communication with backend
- **React Router**: Client-side routing
- **TypeScript**: Type safety and better development experience

## Project Structure

```
ui/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── WorldView.tsx
│   │   ├── ActorList.tsx
│   │   ├── LocationMap.tsx
│   │   ├── TimeControls.tsx
│   │   ├── ActorDetail.tsx
│   │   └── common/
│   ├── hooks/
│   │   ├── useWebSocket.ts
│   │   ├── useSimulation.ts
│   │   └── useWorldState.ts
│   ├── services/
│   │   ├── api.ts
│   │   └── websocket.ts
│   ├── types/
│   │   ├── world.ts
│   │   ├── actor.ts
│   │   └── api.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   └── constants.ts
│   ├── App.tsx
│   └── index.tsx
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

## Development Setup

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

## API Integration

The frontend will connect to the FastAPI backend at `http://localhost:8000` and use:

- REST endpoints for initial data loading and configuration
- WebSocket connections for real-time updates
- Authentication for user management
- Error handling and retry logic

## Design System

### Color Palette
- **Primary**: Blue tones for main UI elements
- **Success**: Green for positive states and actions
- **Warning**: Yellow/orange for alerts and moderate resource levels
- **Danger**: Red for critical states and errors
- **Neutral**: Gray tones for backgrounds and secondary text

### Typography
- **Headers**: Bold, clear hierarchy
- **Body**: Readable sans-serif font
- **Code**: Monospace for IDs and technical data

### Layout
- **Responsive**: Mobile-first design with desktop enhancements
- **Grid System**: Consistent spacing and alignment
- **Cards**: Contained components for different data types
- **Modals**: Overlay dialogs for detailed interactions

This frontend will provide an intuitive, real-time interface for observing and controlling the life_state simulation.