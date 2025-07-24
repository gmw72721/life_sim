"""
Tests for the FastAPI backend.

Basic tests covering REST endpoints and WebSocket connections.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from life_state.api import app, sim_manager


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestRESTEndpoints:
    """Test REST API endpoints."""
    
    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_get_worlds(self, client):
        """Test getting available worlds."""
        response = client.get("/api/worlds")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # Should have at least the default world
        
        # Check structure of world response
        world = data[0]
        assert "world_id" in world
        assert "prob_mass" in world
    
    def test_get_world_tick(self, client):
        """Test getting world state at a specific tick."""
        world_id = "main"
        tick_n = 0
        
        response = client.get(f"/api/worlds/{world_id}/tick/{tick_n}")
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "clock" in data
        assert "actors" in data
        assert "world_stats" in data
        
        # Check world stats structure
        world_stats = data["world_stats"]
        assert "avg_hunger" in world_stats
        assert "avg_fatigue" in world_stats
        assert "avg_mood" in world_stats
        assert "sleeping_cnt" in world_stats
        assert "worlds_alive" in world_stats
    
    def test_start_simulation(self, client):
        """Test starting a simulation."""
        world_id = "main"
        
        response = client.post(f"/api/worlds/{world_id}/start")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert world_id in data["message"]
    
    def test_stop_simulation(self, client):
        """Test stopping a simulation."""
        world_id = "main"
        
        response = client.post(f"/api/worlds/{world_id}/stop")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert world_id in data["message"]


class TestSimulationManager:
    """Test the SimulationManager class."""
    
    def test_get_world_creates_default(self):
        """Test that getting a world creates it if it doesn't exist."""
        manager = sim_manager
        world_id = "test_world"
        
        # Clear any existing world
        if world_id in manager.worlds:
            del manager.worlds[world_id]
        
        world = manager.get_world(world_id)
        assert world is not None
        assert world.world_id == world_id
        assert world_id in manager.worlds
    
    def test_get_world_stats_empty(self):
        """Test world stats calculation with no actors."""
        manager = sim_manager
        world_id = "empty_world"
        
        world = manager.get_world(world_id)
        world.actors.clear()  # Remove all actors
        
        stats = manager.get_world_stats(world)
        assert stats.avg_hunger == 0
        assert stats.avg_fatigue == 0
        assert stats.avg_mood == 0
        assert stats.sleeping_cnt == 0
        assert stats.worlds_alive >= 1
    
    def test_get_world_stats_with_actors(self):
        """Test world stats calculation with actors."""
        manager = sim_manager
        world_id = "test_world_with_actors"
        
        world = manager.get_world(world_id)
        
        # Should have default actors from initialization
        if len(world.actors) > 0:
            stats = manager.get_world_stats(world)
            assert isinstance(stats.avg_hunger, float)
            assert isinstance(stats.avg_fatigue, float)
            assert isinstance(stats.avg_mood, float)
            assert isinstance(stats.sleeping_cnt, int)
            assert stats.worlds_alive >= 1
    
    def test_get_tick_data(self):
        """Test tick data generation."""
        manager = sim_manager
        world_id = "main"
        tick_n = 0
        
        tick_data = manager.get_tick_data(world_id, tick_n)
        
        assert tick_data.clock is not None
        assert isinstance(tick_data.actors, list)
        assert tick_data.world_stats is not None
        
        # Check that actors have required fields
        for actor in tick_data.actors:
            assert hasattr(actor, 'id')
            assert hasattr(actor, 'name')
            assert hasattr(actor, 'state')
            assert hasattr(actor, 'location')
            assert hasattr(actor, 'hunger')
            assert hasattr(actor, 'fatigue')
            assert hasattr(actor, 'mood')


class TestWebSocketConnection:
    """Test WebSocket functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """Test WebSocket connection establishment."""
        world_id = "main"
        
        with client.websocket_connect(f"/ws/worlds/{world_id}") as websocket:
            # Should receive initial data
            data = websocket.receive_json()
            
            assert "clock" in data
            assert "actors" in data
            assert "world_stats" in data
    
    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(self, client):
        """Test multiple WebSocket connections to the same world."""
        world_id = "main"
        
        with client.websocket_connect(f"/ws/worlds/{world_id}") as ws1:
            with client.websocket_connect(f"/ws/worlds/{world_id}") as ws2:
                # Both should receive initial data
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert "clock" in data1
                assert "clock" in data2


@pytest.mark.integration
class TestIntegration:
    """Integration tests combining multiple components."""
    
    def test_full_simulation_flow(self, client):
        """Test a complete simulation workflow."""
        world_id = "integration_test"
        
        # 1. Get initial world state
        response = client.get(f"/api/worlds/{world_id}/tick/0")
        assert response.status_code == 200
        initial_data = response.json()
        
        # 2. Start simulation
        response = client.post(f"/api/worlds/{world_id}/start")
        assert response.status_code == 200
        
        # 3. Get updated state (should be different tick)
        response = client.get(f"/api/worlds/{world_id}/tick/1")
        assert response.status_code == 200
        updated_data = response.json()
        
        # Clock should have advanced (in a real simulation)
        # For this test, we just check structure is maintained
        assert "clock" in updated_data
        assert "actors" in updated_data
        assert "world_stats" in updated_data
        
        # 4. Stop simulation
        response = client.post(f"/api/worlds/{world_id}/stop")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])