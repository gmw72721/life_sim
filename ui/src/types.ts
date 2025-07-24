export interface Actor {
  id: string;
  name: string;
  state: string;
  location: string;
  hunger: number;
  fatigue: number;
  mood: number;
}

export interface WorldStats {
  avg_hunger: number;
  avg_fatigue: number;
  avg_mood: number;
  sleeping_cnt: number;
  worlds_alive: number;
}

export interface TickData {
  clock: string;
  actors: Actor[];
  world_stats: WorldStats;
}

export interface World {
  world_id: string;
  prob_mass: number;
}

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: number;
}