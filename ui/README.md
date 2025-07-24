# Life State Dashboard

A professional React + Tailwind CSS dashboard for monitoring the Life State simulation in real-time.

## Features

- **Real-time Dashboard**: Live view of all actors with WebSocket updates
- **World Statistics**: Comprehensive metrics with interactive charts
- **Responsive Design**: Mobile-friendly interface with adaptive layouts
- **Modern UI**: Built with Tailwind CSS and Framer Motion animations
- **Professional Components**: Collapsible sidebar, data tables, and radial charts

## Tech Stack

- **React 19** with TypeScript
- **Tailwind CSS v3** for styling
- **Vite** for fast development and building
- **Recharts** for data visualization
- **Framer Motion** for smooth animations
- **Lucide React** for icons
- **React Router** for navigation

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- FastAPI backend running on port 8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The development server will start on `http://localhost:5173` with API proxy to `http://localhost:8000`.

### Building for Production

```bash
# Build the application
npm run build

# Preview the build
npm run preview
```

## Development

### Project Structure

```
src/
├── components/          # React components
│   ├── DashboardTable.tsx
│   ├── WorldStatsPanel.tsx
│   └── Sidebar.tsx
├── hooks/              # Custom React hooks
│   └── useWebSocket.ts
├── types.ts            # TypeScript type definitions
├── App.tsx             # Main application component
└── main.tsx           # Application entry point
```

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests
- `npm run lint` - Run ESLint

### API Integration

The frontend connects to the FastAPI backend via:

- **REST API**: `/api/worlds`, `/api/worlds/{id}/tick/{n}`
- **WebSocket**: `/ws/worlds/{id}` for real-time updates

### Styling

The application uses Tailwind CSS with custom components:

- `.card` - Standard card container
- `.btn-primary` / `.btn-secondary` - Button styles
- `.sidebar-item` - Navigation item styles
- Custom animations and responsive breakpoints

## Components

### DashboardTable

Displays actor data in a responsive table/card layout:
- Desktop: Full table with sortable columns
- Mobile: Stacked card layout
- Real-time updates with smooth animations

### WorldStatsPanel

Shows world statistics with:
- Overview metric cards
- Radial progress charts (Recharts)
- Population health summary
- Real-time data visualization

### Sidebar

Collapsible navigation with:
- World selection dropdown
- Connection status indicator
- Navigation menu with icons
- Responsive design

## Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm test -- --watch

# Run tests with coverage
npm test -- --coverage
```

Tests cover:
- WebSocket hook functionality
- Component rendering
- User interactions
- Error handling

## Performance

- Bundle size kept under 200KB uncompressed
- Tree-shaking for Lucide icons and Recharts
- Lazy loading for route components
- Optimized WebSocket reconnection logic

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation as needed
4. Ensure responsive design works on all breakpoints
