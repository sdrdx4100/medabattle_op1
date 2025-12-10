"""
Simulation utilities for batch battle testing.

This module provides tools for:
- Running multiple battles with specified configurations
- Collecting and aggregating results
- Exporting results for analysis
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .battle_logic import (
    AggressiveStrategy,
    BattleManager,
    BattleState,
    DefensiveStrategy,
    MedalBasedStrategy,
    RandomStrategy,
    Strategy,
)
from .models import Robot, create_sample_robot


@dataclass
class SimulationResult:
    """
    Result of a single simulated battle.
    
    Attributes:
        battle_id: Unique identifier for the battle
        winner: Winning team (0, 1, or None for draw)
        turns: Total turns taken
        team_a_remaining: Functional robots remaining on team A
        team_b_remaining: Functional robots remaining on team B
        total_damage_a: Total damage dealt by team A
        total_damage_b: Total damage dealt by team B
        config_name: Name of the configuration used
    """
    battle_id: int
    winner: int | None
    turns: int
    team_a_remaining: int
    team_b_remaining: int
    total_damage_a: int = 0
    total_damage_b: int = 0
    config_name: str = "default"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "battle_id": self.battle_id,
            "winner": self.winner,
            "turns": self.turns,
            "team_a_remaining": self.team_a_remaining,
            "team_b_remaining": self.team_b_remaining,
            "total_damage_a": self.total_damage_a,
            "total_damage_b": self.total_damage_b,
            "config_name": self.config_name,
        }


@dataclass
class SimulationConfig:
    """
    Configuration for a simulation run.
    
    Attributes:
        name: Configuration name
        team_a_size: Number of robots on team A
        team_b_size: Number of robots on team B
        team_a_strategy: Strategy name for team A
        team_b_strategy: Strategy name for team B
        max_turns: Maximum turns per battle
        seed: Random seed (None for random)
    """
    name: str = "default"
    team_a_size: int = 3
    team_b_size: int = 3
    team_a_strategy: str = "medal"
    team_b_strategy: str = "aggressive"
    max_turns: int = 1000
    seed: int | None = None
    team_a_robots: list[dict[str, Any]] = field(default_factory=list)
    team_b_robots: list[dict[str, Any]] = field(default_factory=list)
    
    @classmethod
    def from_yaml(cls, path: Path | str) -> SimulationConfig:
        """Load configuration from YAML file."""
        import yaml
        
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data.get("name", "default"),
            team_a_size=data.get("team_a_size", 3),
            team_b_size=data.get("team_b_size", 3),
            team_a_strategy=data.get("team_a_strategy", "medal"),
            team_b_strategy=data.get("team_b_strategy", "aggressive"),
            max_turns=data.get("max_turns", 1000),
            seed=data.get("seed"),
            team_a_robots=data.get("team_a_robots", []),
            team_b_robots=data.get("team_b_robots", []),
        )
    
    def to_yaml(self, path: Path | str) -> None:
        """Save configuration to YAML file."""
        import yaml
        
        path = Path(path)
        data = {
            "name": self.name,
            "team_a_size": self.team_a_size,
            "team_b_size": self.team_b_size,
            "team_a_strategy": self.team_a_strategy,
            "team_b_strategy": self.team_b_strategy,
            "max_turns": self.max_turns,
            "seed": self.seed,
            "team_a_robots": self.team_a_robots,
            "team_b_robots": self.team_b_robots,
        }
        
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False)


def get_strategy(name: str) -> Strategy:
    """
    Get a strategy instance by name.
    
    Args:
        name: Strategy name (random, aggressive, defensive, medal)
        
    Returns:
        Strategy instance
    """
    strategies: dict[str, type[Strategy]] = {
        "random": RandomStrategy,
        "aggressive": AggressiveStrategy,
        "defensive": DefensiveStrategy,
        "medal": MedalBasedStrategy,
    }
    
    strategy_cls = strategies.get(name.lower(), MedalBasedStrategy)
    return strategy_cls()


class Simulator:
    """
    Runs batch battle simulations.
    
    Attributes:
        config: Simulation configuration
        results: List of simulation results
    """
    
    def __init__(self, config: SimulationConfig | None = None):
        """
        Initialize simulator.
        
        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()
        self.results: list[SimulationResult] = []
    
    def _create_battle_state(self) -> BattleState:
        """Create initial battle state from configuration."""
        state = BattleState()
        
        # Create team A
        if self.config.team_a_robots:
            for i, robot_data in enumerate(self.config.team_a_robots):
                robot = Robot.from_dict(robot_data)
                robot.team = 0
                robot.position = (1, i + 1)
                state.team_a.append(robot)
        else:
            for i in range(self.config.team_a_size):
                robot = create_sample_robot(f"PlayerBot_{i+1}", team=0)
                robot.position = (1, i + 1)
                state.team_a.append(robot)
        
        # Create team B
        if self.config.team_b_robots:
            for i, robot_data in enumerate(self.config.team_b_robots):
                robot = Robot.from_dict(robot_data)
                robot.team = 1
                robot.position = (8, i + 1)
                state.team_b.append(robot)
        else:
            for i in range(self.config.team_b_size):
                robot = create_sample_robot(f"EnemyBot_{i+1}", team=1)
                robot.position = (8, i + 1)
                state.team_b.append(robot)
        
        return state
    
    def run_single_battle(self, battle_id: int) -> SimulationResult:
        """
        Run a single battle and return the result.
        
        Args:
            battle_id: Unique identifier for this battle
            
        Returns:
            Simulation result
        """
        state = self._create_battle_state()
        
        strategy_a = get_strategy(self.config.team_a_strategy)
        strategy_b = get_strategy(self.config.team_b_strategy)
        
        manager = BattleManager(
            state=state,
            player_strategy=strategy_a,
            enemy_strategy=strategy_b,
        )
        
        manager.start_battle()
        winner = manager.run_until_complete(self.config.max_turns)
        
        # Calculate total damage from log
        total_damage_a = 0
        total_damage_b = 0
        
        for entry in state.log.entries:
            damage = entry.get("damage", 0)
            if damage > 0:
                # Find actor team from log
                actor_name = entry.get("actor", "")
                if actor_name.startswith("PlayerBot"):
                    total_damage_a += damage
                else:
                    total_damage_b += damage
        
        return SimulationResult(
            battle_id=battle_id,
            winner=winner,
            turns=state.turn_count,
            team_a_remaining=len(state.active_team_a),
            team_b_remaining=len(state.active_team_b),
            total_damage_a=total_damage_a,
            total_damage_b=total_damage_b,
            config_name=self.config.name,
        )
    
    def run_simulation(self, n_matches: int) -> list[SimulationResult]:
        """
        Run multiple battles.
        
        Args:
            n_matches: Number of battles to run
            
        Returns:
            List of simulation results
        """
        import random
        
        if self.config.seed is not None:
            random.seed(self.config.seed)
        
        self.results = []
        
        for i in range(n_matches):
            result = self.run_single_battle(i)
            self.results.append(result)
        
        return self.results
    
    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics of simulation results.
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.results:
            return {}
        
        total = len(self.results)
        team_a_wins = sum(1 for r in self.results if r.winner == 0)
        team_b_wins = sum(1 for r in self.results if r.winner == 1)
        draws = sum(1 for r in self.results if r.winner is None)
        
        avg_turns = sum(r.turns for r in self.results) / total
        avg_damage_a = sum(r.total_damage_a for r in self.results) / total
        avg_damage_b = sum(r.total_damage_b for r in self.results) / total
        
        return {
            "total_battles": total,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "draws": draws,
            "team_a_win_rate": team_a_wins / total * 100,
            "team_b_win_rate": team_b_wins / total * 100,
            "average_turns": avg_turns,
            "average_damage_a": avg_damage_a,
            "average_damage_b": avg_damage_b,
        }
    
    def export_to_csv(self, path: Path | str) -> None:
        """
        Export results to CSV file.
        
        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "battle_id",
                    "winner",
                    "turns",
                    "team_a_remaining",
                    "team_b_remaining",
                    "total_damage_a",
                    "total_damage_b",
                    "config_name",
                ],
            )
            writer.writeheader()
            for result in self.results:
                writer.writerow(result.to_dict())
    
    def export_to_json(self, path: Path | str) -> None:
        """
        Export results to JSON file.
        
        Args:
            path: Output file path
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "config": {
                "name": self.config.name,
                "team_a_strategy": self.config.team_a_strategy,
                "team_b_strategy": self.config.team_b_strategy,
            },
            "summary": self.get_summary(),
            "results": [r.to_dict() for r in self.results],
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def run_simulation(
    config: SimulationConfig | Path | str,
    n_matches: int,
) -> list[SimulationResult]:
    """
    Convenience function to run a simulation.
    
    Args:
        config: Configuration or path to configuration file
        n_matches: Number of battles to run
        
    Returns:
        List of simulation results
    """
    if isinstance(config, (str, Path)):
        config = SimulationConfig.from_yaml(config)
    
    simulator = Simulator(config)
    return simulator.run_simulation(n_matches)
