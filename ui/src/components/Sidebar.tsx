import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  ChevronLeft, 
  ChevronRight, 
  Home, 
  BarChart3, 
  Globe, 
  Settings,
  Wifi,
  WifiOff
} from 'lucide-react';

interface SidebarProps {
  currentWorld: string;
  availableWorlds: string[];
  onWorldChange: (worldId: string) => void;
  isConnected: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentWorld,
  availableWorlds,
  onWorldChange,
  isConnected,
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const navigationItems = [
    { path: '/', icon: Home, label: 'Dashboard' },
    { path: '/world', icon: BarChart3, label: 'World Stats' },
  ];

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className={`bg-white border-r border-gray-200 transition-all duration-300 ${
      isCollapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <Globe className="w-6 h-6 text-primary-600" />
              <h1 className="text-lg font-semibold text-gray-900">Life State</h1>
            </div>
          )}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors"
          >
            {isCollapsed ? (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronLeft className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>

        {/* Connection Status */}
        <div className="px-4 py-2 border-b border-gray-200">
          <div className={`flex items-center space-x-2 ${isCollapsed ? 'justify-center' : ''}`}>
            {isConnected ? (
              <Wifi className="w-4 h-4 text-green-500" />
            ) : (
              <WifiOff className="w-4 h-4 text-red-500" />
            )}
            {!isCollapsed && (
              <span className={`text-xs font-medium ${
                isConnected ? 'text-green-700' : 'text-red-700'
              }`}>
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
        </div>

        {/* World Selection */}
        {!isCollapsed && (
          <div className="px-4 py-3 border-b border-gray-200">
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Current World
            </label>
            <select
              value={currentWorld}
              onChange={(e) => onWorldChange(e.target.value)}
              className="w-full text-sm border border-gray-300 rounded-md px-3 py-1 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {availableWorlds.map((worldId) => (
                <option key={worldId} value={worldId}>
                  {worldId}
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`sidebar-item ${
                  active ? 'sidebar-item-active' : 'sidebar-item-inactive'
                } ${isCollapsed ? 'justify-center px-2' : ''}`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon className={`w-5 h-5 ${isCollapsed ? '' : 'mr-3'}`} />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200">
          <div className={`flex items-center ${isCollapsed ? 'justify-center' : 'space-x-2'}`}>
            <Settings className="w-4 h-4 text-gray-400" />
            {!isCollapsed && (
              <span className="text-xs text-gray-500">v1.0.0</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};