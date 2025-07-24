import React from 'react';
import { motion } from 'framer-motion';
import { RadialBarChart, RadialBar, ResponsiveContainer } from 'recharts';
import type { WorldStats } from '../types';
import { 
  Activity, 
  Coffee, 
  Zap, 
  Heart, 
  Moon, 
  Globe,
  TrendingUp,
  Users
} from 'lucide-react';

interface WorldStatsPanelProps {
  stats: WorldStats;
  isLoading?: boolean;
}

interface RadialChartData {
  name: string;
  value: number;
  fill: string;
}

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
  trend?: number;
}> = ({ title, value, icon, color, trend }) => (
  <motion.div
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ opacity: 1, scale: 1 }}
    className="card"
    whileHover={{ scale: 1.02 }}
    transition={{ duration: 0.2 }}
  >
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        {trend !== undefined && (
          <div className="flex items-center mt-1">
            <TrendingUp className={`w-3 h-3 ${trend >= 0 ? 'text-green-500' : 'text-red-500'}`} />
            <span className={`text-xs ml-1 ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {trend >= 0 ? '+' : ''}{trend.toFixed(1)}%
            </span>
          </div>
        )}
      </div>
      <div className={`p-3 rounded-full ${color}`}>
        {icon}
      </div>
    </div>
  </motion.div>
);

const RadialGauge: React.FC<{
  title: string;
  value: number;
  max: number;
  color: string;
  icon: React.ReactNode;
}> = ({ title, value, max, color, icon }) => {
  const percentage = Math.min(Math.max(value, 0), max);
  const data: RadialChartData[] = [
    {
      name: title,
      value: percentage,
      fill: color,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="card text-center"
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-center mb-2">
        {icon}
        <h3 className="text-lg font-semibold text-gray-900 ml-2">{title}</h3>
      </div>
      
      <div className="relative w-32 h-32 mx-auto mb-4">
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="90%"
            data={data}
            startAngle={90}
            endAngle={-270}
          >
            <RadialBar
              dataKey="value"
              cornerRadius={10}
              fill={color}
            />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              {percentage.toFixed(1)}
            </div>
            <div className="text-xs text-gray-500">
              {max === 100 ? '%' : `/${max}`}
            </div>
          </div>
        </div>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-500"
          style={{ 
            width: `${(percentage / max) * 100}%`,
            backgroundColor: color 
          }}
        />
      </div>
    </motion.div>
  );
};

export const WorldStatsPanel: React.FC<WorldStatsPanelProps> = ({ 
  stats, 
  isLoading = false 
}) => {
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="card">
          <div className="animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-4"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-24 bg-gray-100 rounded"></div>
              ))}
            </div>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card">
              <div className="animate-pulse">
                <div className="w-32 h-32 bg-gray-200 rounded-full mx-auto mb-4"></div>
                <div className="h-4 bg-gray-200 rounded"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Sleeping Actors"
          value={stats.sleeping_cnt}
          icon={<Moon className="w-5 h-5 text-blue-600" />}
          color="bg-blue-100"
        />
        
        <StatCard
          title="Active Worlds"
          value={stats.worlds_alive}
          icon={<Globe className="w-5 h-5 text-green-600" />}
          color="bg-green-100"
        />
        
        <StatCard
          title="Avg Hunger"
          value={`${stats.avg_hunger.toFixed(1)}%`}
          icon={<Coffee className="w-5 h-5 text-orange-600" />}
          color="bg-orange-100"
        />
        
        <StatCard
          title="Avg Fatigue"
          value={`${stats.avg_fatigue.toFixed(1)}%`}
          icon={<Zap className="w-5 h-5 text-purple-600" />}
          color="bg-purple-100"
        />
      </div>

      {/* Radial Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <RadialGauge
          title="Average Hunger"
          value={stats.avg_hunger}
          max={100}
          color="#f97316"
          icon={<Coffee className="w-5 h-5 text-orange-600" />}
        />
        
        <RadialGauge
          title="Average Fatigue"
          value={stats.avg_fatigue}
          max={100}
          color="#8b5cf6"
          icon={<Zap className="w-5 h-5 text-purple-600" />}
        />
        
        <RadialGauge
          title="Average Mood"
          value={((stats.avg_mood + 2) / 4) * 100} // Convert -2 to 2 range to 0-100
          max={100}
          color="#10b981"
          icon={<Heart className="w-5 h-5 text-green-600" />}
        />
      </div>

      {/* Detailed Metrics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Activity className="w-5 h-5 text-gray-600 mr-2" />
          Simulation Metrics
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600 mb-2">
              {stats.sleeping_cnt}
            </div>
            <div className="text-sm text-gray-600">Actors Sleeping</div>
            <div className="w-full bg-blue-100 rounded-full h-2 mt-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${(stats.sleeping_cnt / 20) * 100}%` }}
              />
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600 mb-2">
              {stats.worlds_alive}
            </div>
            <div className="text-sm text-gray-600">Active Worlds</div>
            <div className="w-full bg-green-100 rounded-full h-2 mt-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(stats.worlds_alive * 20, 100)}%` }}
              />
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600 mb-2">
              {stats.avg_mood.toFixed(2)}
            </div>
            <div className="text-sm text-gray-600">Mood Score</div>
            <div className="w-full bg-purple-100 rounded-full h-2 mt-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${((stats.avg_mood + 2) / 4) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Health Summary */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Users className="w-5 h-5 text-gray-600 mr-2" />
          Population Health Summary
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Hunger Level</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${stats.avg_hunger}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 min-w-[3rem]">
                {stats.avg_hunger.toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Fatigue Level</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${stats.avg_fatigue}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 min-w-[3rem]">
                {stats.avg_fatigue.toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Mood Level</span>
            <div className="flex items-center space-x-2">
              <div className="w-32 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${((stats.avg_mood + 2) / 4) * 100}%` }}
                />
              </div>
              <span className="text-sm text-gray-600 min-w-[3rem]">
                {stats.avg_mood.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};