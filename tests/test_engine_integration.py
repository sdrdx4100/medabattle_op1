"""
Tests for C++ engine integration.

These tests verify the integration between Python and C++ components.
When the C++ engine is not available, they test the Python fallbacks.
"""

import pytest

from src.core.models import create_sample_robot, PartType
from src.core.battle_logic import (
    Action,
    BattleManager,
    BattleState,
    RandomStrategy,
)
from src.engine import HAS_CPP_ENGINE


class TestEngineAvailability:
    """Tests for engine availability detection."""
    
    def test_engine_flag_exists(self):
        """Test that HAS_CPP_ENGINE flag is defined."""
        assert isinstance(HAS_CPP_ENGINE, bool)
    
    def test_fallback_when_unavailable(self):
        """Test that fallback functions exist when C++ unavailable."""
        from src.engine import simulate_action, update_atb
        
        # These should exist regardless of C++ availability
        assert callable(simulate_action)
        assert callable(update_atb)


class TestBattleManagerIntegration:
    """Tests for BattleManager with engine integration."""
    
    def setup_method(self):
        """Set up test battle."""
        self.state = BattleState()
        
        player = create_sample_robot("Player", team=0)
        enemy = create_sample_robot("Enemy", team=1)
        
        self.state.team_a.append(player)
        self.state.team_b.append(enemy)
        
        self.manager = BattleManager(
            state=self.state,
            player_strategy=RandomStrategy(),
            enemy_strategy=RandomStrategy(),
        )
    
    def test_manager_works_without_cpp(self):
        """Test that battle manager works with Python fallback."""
        self.manager.start_battle()
        
        # Should be able to run battle
        winner = self.manager.run_until_complete(max_turns=100)
        
        assert winner in (0, 1, None)
    
    def test_action_calculation_fallback(self):
        """Test action calculation with Python fallback."""
        self.manager.start_battle()
        
        actor = self.state.team_a[0]
        target = self.state.team_b[0]
        actor.atb_gauge = 100
        
        action = Action(
            actor=actor,
            part=actor.right_arm,
            target=target,
            target_part=PartType.HEAD,
        )
        
        result = self.manager.execute_action(action)
        
        # Should get valid result
        assert hasattr(result, 'hit')
        assert hasattr(result, 'damage')
        assert hasattr(result, 'effect')
    
    def test_atb_update_fallback(self):
        """Test ATB update with Python fallback."""
        self.manager.start_battle()
        
        initial_gauges = [r.atb_gauge for r in self.state.all_robots]
        
        self.manager.advance_time(20.0)
        
        # All functional robots should have higher ATB
        for robot, initial in zip(self.state.all_robots, initial_gauges):
            if robot.is_functional:
                assert robot.atb_gauge > initial


@pytest.mark.skipif(not HAS_CPP_ENGINE, reason="C++ engine not available")
class TestCppEngine:
    """Tests that require the C++ engine."""
    
    def test_simulate_action(self):
        """Test C++ simulate_action function."""
        from src.engine import simulate_action
        
        action_dict = {
            "actor_name": "TestBot",
            "actor_team": 0,
            "part_name": "Blaster Arm",
            "action_type": "SHOOT",
            "success_value": 55,
            "power": 40,
            "hit_bonus": 5,
            "target_name": "Enemy",
            "target_team": 1,
            "target_evade": 10,
            "target_part": "HEAD",
        }
        
        result = simulate_action(action_dict)
        
        assert "hit" in result
        assert "damage" in result
        assert "effect" in result
    
    def test_update_atb(self):
        """Test C++ update_atb function."""
        from src.engine import update_atb
        
        state_dict = {
            "team_a": [
                {
                    "name": "Player1",
                    "atb_gauge": 50.0,
                    "legs": {"charge": 20},
                    "head": {"armor": 30},
                },
            ],
            "team_b": [
                {
                    "name": "Enemy1",
                    "atb_gauge": 30.0,
                    "legs": {"charge": 25},
                    "head": {"armor": 30},
                },
            ],
        }
        
        result = update_atb(state_dict, 10.0)
        
        assert "robots" in result
        assert len(result["robots"]) == 2
        
        # ATB should have increased
        for robot in result["robots"]:
            assert "atb_gauge" in robot
            assert robot["atb_gauge"] > 30.0


class TestSimulator:
    """Tests for the simulation system."""
    
    def test_run_simulation(self):
        """Test running a batch simulation."""
        from src.core.simulator import Simulator, SimulationConfig
        
        config = SimulationConfig(
            name="test",
            team_a_size=2,
            team_b_size=2,
            team_a_strategy="random",
            team_b_strategy="aggressive",
            max_turns=200,
        )
        
        simulator = Simulator(config)
        results = simulator.run_simulation(n_matches=5)
        
        assert len(results) == 5
        
        for result in results:
            assert result.winner in (0, 1, None)
            assert result.turns > 0
    
    def test_simulation_summary(self):
        """Test getting simulation summary."""
        from src.core.simulator import Simulator, SimulationConfig
        
        config = SimulationConfig(max_turns=100)
        simulator = Simulator(config)
        simulator.run_simulation(n_matches=10)
        
        summary = simulator.get_summary()
        
        assert "total_battles" in summary
        assert summary["total_battles"] == 10
        assert "team_a_win_rate" in summary
        assert "average_turns" in summary
    
    def test_simulation_export(self, tmp_path):
        """Test exporting simulation results."""
        from src.core.simulator import Simulator, SimulationConfig
        
        config = SimulationConfig(max_turns=100)
        simulator = Simulator(config)
        simulator.run_simulation(n_matches=5)
        
        # Export to CSV
        csv_path = tmp_path / "results.csv"
        simulator.export_to_csv(csv_path)
        assert csv_path.exists()
        
        # Export to JSON
        json_path = tmp_path / "results.json"
        simulator.export_to_json(json_path)
        assert json_path.exists()
