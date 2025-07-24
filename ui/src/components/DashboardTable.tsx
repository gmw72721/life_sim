import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Actor } from '../types';
import { User, MapPin, Zap, Coffee, Heart } from 'lucide-react';

interface DashboardTableProps {
  actors: Actor[];
  isLoading?: boolean;
}

interface Column {
  id: keyof Actor;
  header: string;
  accessor: (actor: Actor) => string | number;
  render?: (value: any, actor: Actor) => React.ReactNode;
}

const getStateColor = (state: string): string => {
  const stateColors: Record<string, string> = {
    'Sleeping': 'bg-blue-100 text-blue-800',
    'Waking_Up': 'bg-yellow-100 text-yellow-800',
    'Idle': 'bg-gray-100 text-gray-800',
    'Transitioning': 'bg-purple-100 text-purple-800',
    'Driving': 'bg-green-100 text-green-800',
    'Walking': 'bg-orange-100 text-orange-800',
    'Focused_Work': 'bg-red-100 text-red-800',
    'Eating': 'bg-pink-100 text-pink-800',
  };
  return stateColors[state] || 'bg-gray-100 text-gray-800';
};

const getResourceBar = (value: number, max: number = 100, color: string): React.ReactNode => {
  const percentage = Math.min(Math.max(value, 0), max);
  const width = (percentage / max) * 100;
  
  return (
    <div className="flex items-center space-x-2">
      <div className="w-16 bg-gray-200 rounded-full h-2 relative">
        <div
          className={`h-2 rounded-full transition-all duration-300 ${color}`}
          style={{ width: `${width}%` }}
        />
      </div>
      <span className="text-xs text-gray-600 min-w-[3rem]">
        {percentage.toFixed(0)}%
      </span>
    </div>
  );
};

const getMoodDisplay = (mood: number): React.ReactNode => {
  let emoji = '😐';
  
  if (mood > 1) {
    emoji = '😄';
  } else if (mood > 0) {
    emoji = '🙂';
  } else if (mood < -1) {
    emoji = '😢';
  } else if (mood < 0) {
    emoji = '😔';
  }
  
  return (
    <div className="flex items-center space-x-2">
      <span className="text-lg">{emoji}</span>
      <span className="text-xs text-gray-600">
        {mood.toFixed(1)}
      </span>
    </div>
  );
};

export const DashboardTable: React.FC<DashboardTableProps> = ({ 
  actors, 
  isLoading = false 
}) => {
  const columns: Column[] = useMemo(() => [
    {
      id: 'name',
      header: 'Name',
      accessor: (actor) => actor.name,
      render: (value, actor) => (
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-primary-600" />
          </div>
          <div>
            <div className="font-medium text-gray-900">{value}</div>
            <div className="text-xs text-gray-500">ID: {actor.id.slice(0, 8)}</div>
          </div>
        </div>
      ),
    },
    {
      id: 'state',
      header: 'Current State',
      accessor: (actor) => actor.state,
      render: (value) => (
        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStateColor(value)}`}>
          {value.replace('_', ' ')}
        </span>
      ),
    },
    {
      id: 'location',
      header: 'Location',
      accessor: (actor) => actor.location,
      render: (value) => (
        <div className="flex items-center space-x-2">
          <MapPin className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-900">{value}</span>
        </div>
      ),
    },
    {
      id: 'hunger',
      header: 'Hunger %',
      accessor: (actor) => actor.hunger,
      render: (value) => getResourceBar(value, 100, 'bg-orange-500'),
    },
    {
      id: 'fatigue',
      header: 'Fatigue %',
      accessor: (actor) => actor.fatigue,
      render: (value) => getResourceBar(value, 100, 'bg-blue-500'),
    },
    {
      id: 'mood',
      header: 'Mood',
      accessor: (actor) => actor.mood,
      render: (value) => getMoodDisplay(value),
    },
  ], []);

  if (isLoading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Actor Dashboard</h2>
        <p className="text-sm text-gray-600">
          Real-time view of all {actors.length} actors in the simulation
        </p>
      </div>

      {/* Desktop Table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="table-auto w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              {columns.map((column) => (
                <th
                  key={column.id}
                  className="text-left py-3 px-4 font-medium text-gray-700"
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <AnimatePresence>
              {actors.map((actor, index) => (
                <motion.tr
                  key={actor.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                  className="table-row"
                  whileHover={{ backgroundColor: '#f9fafb' }}
                >
                  {columns.map((column) => (
                    <td key={column.id} className="py-3 px-4">
                      {column.render
                        ? column.render(column.accessor(actor), actor)
                        : column.accessor(actor)}
                    </td>
                  ))}
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
      </div>

      {/* Mobile Cards */}
      <div className="md:hidden space-y-4">
        <AnimatePresence>
          {actors.map((actor, index) => (
            <motion.div
              key={actor.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.2, delay: index * 0.05 }}
              className="bg-gray-50 rounded-lg p-4 border border-gray-200"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">{actor.name}</div>
                    <div className="text-xs text-gray-500">ID: {actor.id.slice(0, 8)}</div>
                  </div>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStateColor(actor.state)}`}>
                  {actor.state.replace('_', ' ')}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <MapPin className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-700">Location</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900">{actor.location}</span>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="flex items-center space-x-1 mb-1">
                      <Coffee className="w-3 h-3 text-orange-500" />
                      <span className="text-xs text-gray-600">Hunger</span>
                    </div>
                    {getResourceBar(actor.hunger, 100, 'bg-orange-500')}
                  </div>
                  
                  <div>
                    <div className="flex items-center space-x-1 mb-1">
                      <Zap className="w-3 h-3 text-blue-500" />
                      <span className="text-xs text-gray-600">Fatigue</span>
                    </div>
                    {getResourceBar(actor.fatigue, 100, 'bg-blue-500')}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Heart className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-gray-700">Mood</span>
                  </div>
                  {getMoodDisplay(actor.mood)}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {actors.length === 0 && !isLoading && (
        <div className="text-center py-12">
          <User className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No actors found</h3>
          <p className="text-gray-600">
            No actors are currently active in this world.
          </p>
        </div>
      )}
    </div>
  );
};