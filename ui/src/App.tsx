import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, Play, Pause, RotateCcw } from 'lucide-react';

import { Sidebar } from './components/Sidebar';
import { DashboardTable } from './components/DashboardTable';
import { WorldStatsPanel } from './components/WorldStatsPanel';
import { useWebSocket } from './hooks/useWebSocket';
import type { World, TickData } from './types';

// Dashboard Page Component
const DashboardPage: React.FC<{ data: TickData | null; isLoading: boolean }> = ({ 
  data, 
  isLoading 
}) => (
  <div className="space-y-6">
    <DashboardTable 
      actors={data?.actors || []} 
      isLoading={isLoading}
    />
  </div>
);

// World Stats Page Component
const WorldStatsPage: React.FC<{ data: TickData | null; isLoading: boolean }> = ({ 
  data, 
  isLoading 
}) => (
  <div className="space-y-6">
    <WorldStatsPanel 
      stats={data?.world_stats || {
        avg_hunger: 0,
        avg_fatigue: 0,
        avg_mood: 0,
        sleeping_cnt: 0,
        worlds_alive: 0
      }} 
      isLoading={isLoading}
    />
  </div>
);

// Top Navigation Bar Component
const TopNavBar: React.FC<{
  currentTime: string;
  tickCount: number;
  isSimulationRunning: boolean;
  onToggleSimulation: () => void;
  onResetSimulation: () => void;
}> = ({ 
  currentTime, 
  tickCount, 
  isSimulationRunning, 
  onToggleSimulation, 
  onResetSimulation 
}) => (
  <div className="bg-white border-b border-gray-200 px-6 py-4">
    <div className="flex items-center justify-between">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <Clock className="w-5 h-5 text-gray-500" />
          <div>
            <div className="text-sm font-medium text-gray-900">
              {currentTime ? new Date(currentTime).toLocaleString() : 'Not connected'}
            </div>
            <div className="text-xs text-gray-500">
              Tick #{tickCount}
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex items-center space-x-3">
        <button
          onClick={onToggleSimulation}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium text-sm transition-colors ${
            isSimulationRunning
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : 'bg-green-100 text-green-700 hover:bg-green-200'
          }`}
        >
          {isSimulationRunning ? (
            <>
              <Pause className="w-4 h-4" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              <span>Start</span>
            </>
          )}
        </button>
        
        <button
          onClick={onResetSimulation}
          className="flex items-center space-x-2 px-4 py-2 rounded-md font-medium text-sm bg-gray-100 text-gray-700 hover:bg-gray-200 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Reset</span>
        </button>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  const [currentWorld, setCurrentWorld] = useState('main');
  const [availableWorlds, setAvailableWorlds] = useState<string[]>(['main']);
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);
  const [tickCount, setTickCount] = useState(0);

  // WebSocket connection
  const { data, isConnected, error } = useWebSocket(currentWorld, {
    onMessage: () => {
      setTickCount(prev => prev + 1);
    },
    onConnect: () => {
      console.log('Connected to WebSocket');
    },
    onDisconnect: () => {
      console.log('Disconnected from WebSocket');
    },
  });

  // Fetch available worlds on mount
  useEffect(() => {
    const fetchWorlds = async () => {
      try {
        const response = await fetch('/api/worlds');
        if (response.ok) {
          const worlds: World[] = await response.json();
          const worldIds = worlds.map(w => w.world_id);
          setAvailableWorlds(worldIds);
          
          if (worldIds.length > 0 && !worldIds.includes(currentWorld)) {
            setCurrentWorld(worldIds[0]);
          }
        }
      } catch (error) {
        console.error('Failed to fetch worlds:', error);
      }
    };

    fetchWorlds();
  }, [currentWorld]);

  const handleWorldChange = (worldId: string) => {
    setCurrentWorld(worldId);
    setTickCount(0);
  };

  const handleToggleSimulation = async () => {
    try {
      const endpoint = isSimulationRunning 
        ? `/api/worlds/${currentWorld}/stop`
        : `/api/worlds/${currentWorld}/start`;
      
      const response = await fetch(endpoint, { method: 'POST' });
      
      if (response.ok) {
        setIsSimulationRunning(!isSimulationRunning);
      } else {
        console.error('Failed to toggle simulation');
      }
    } catch (error) {
      console.error('Error toggling simulation:', error);
    }
  };

  const handleResetSimulation = async () => {
    try {
      // Stop simulation first
      await fetch(`/api/worlds/${currentWorld}/stop`, { method: 'POST' });
      setIsSimulationRunning(false);
      setTickCount(0);
      
      // Could add logic to reset world state here
      console.log('Simulation reset');
    } catch (error) {
      console.error('Error resetting simulation:', error);
    }
  };

  return (
    <Router>
      <div className="min-h-screen bg-gray-50 flex">
        {/* Sidebar */}
        <Sidebar
          currentWorld={currentWorld}
          availableWorlds={availableWorlds}
          onWorldChange={handleWorldChange}
          isConnected={isConnected}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Top Navigation */}
          <TopNavBar
            currentTime={data?.clock || ''}
            tickCount={tickCount}
            isSimulationRunning={isSimulationRunning}
            onToggleSimulation={handleToggleSimulation}
            onResetSimulation={handleResetSimulation}
          />

          {/* Page Content */}
          <main className="flex-1 p-6 overflow-y-auto">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentWorld}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
              >
                <Routes>
                  <Route 
                    path="/" 
                    element={
                      <DashboardPage 
                        data={data} 
                        isLoading={!isConnected && !error} 
                      />
                    } 
                  />
                  <Route 
                    path="/world" 
                    element={
                      <WorldStatsPage 
                        data={data} 
                        isLoading={!isConnected && !error} 
                      />
                    } 
                  />
                </Routes>
              </motion.div>
            </AnimatePresence>

            {/* Connection Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-md shadow-lg"
              >
                <div className="text-sm font-medium">Connection Error</div>
                <div className="text-xs opacity-90">{error}</div>
              </motion.div>
            )}

            {/* Connection Status */}
            {!isConnected && !error && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="fixed bottom-4 right-4 bg-yellow-500 text-white px-4 py-2 rounded-md shadow-lg"
              >
                <div className="text-sm font-medium">Connecting...</div>
                <div className="text-xs opacity-90">Establishing WebSocket connection</div>
              </motion.div>
            )}
          </main>
        </div>
      </div>
    </Router>
  );
};

export default App;
