"""
Battle logic for Medabot-style robot combat.

This module handles:
- Battle state management
- Turn order and action execution
- AI strategies for action selection
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from .models import ActionType, Part, PartType, Robot


class BattlePhase(Enum):
    """Current phase of the battle."""
    SETUP = auto()
    IN_PROGRESS = auto()
    PLAYER_TURN = auto()
    ENEMY_TURN = auto()
    FINISHED = auto()


@dataclass
class Action:
    """
    Represents a single combat action.
    
    Attributes:
        actor: Robot performing the action
        part: Part being used
        target: Target robot
        target_part: Specific part targeted (optional)
    """
    actor: Robot
    part: Part
    target: Robot
    target_part: PartType | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert action to dictionary for C++ engine."""
        return {
            "actor_name": self.actor.name,
            "actor_team": self.actor.team,
            "part_name": self.part.name,
            "action_type": self.part.action_type.name,
            "success_value": self.part.success_value,
            "power": self.part.power,
            "hit_bonus": self.part.hit_bonus,
            "target_name": self.target.name,
            "target_team": self.target.team,
            "target_evade": self.target.total_evade,
            "target_part": self.target_part.name if self.target_part else None,
        }


@dataclass
class ActionResult:
    """
    Result of executing an action.
    
    Attributes:
        action: The action that was executed
        hit: Whether the action hit
        damage: Damage dealt (if applicable)
        effect: Additional effect description
    """
    action: Action
    hit: bool
    damage: int = 0
    effect: str = ""
    
    def to_log_entry(self) -> dict[str, Any]:
        """Convert to log entry format."""
        return {
            "actor": self.action.actor.name,
            "part": self.action.part.name,
            "target": self.action.target.name,
            "hit": self.hit,
            "damage": self.damage,
            "effect": self.effect,
        }


@dataclass
class BattleLog:
    """Log of battle events."""
    entries: list[dict[str, Any]] = field(default_factory=list)
    
    def add_entry(self, entry: dict[str, Any]) -> None:
        """Add a log entry."""
        self.entries.append(entry)
    
    def add_action_result(self, result: ActionResult) -> None:
        """Add an action result to the log."""
        self.add_entry(result.to_log_entry())
    
    def add_message(self, message: str) -> None:
        """Add a simple message to the log."""
        self.add_entry({"message": message})


@dataclass
class BattleState:
    """
    Complete state of an ongoing battle.
    
    Attributes:
        team_a: List of robots on team A (player)
        team_b: List of robots on team B (enemy)
        turn_count: Current turn number
        phase: Current battle phase
        current_actor: Robot currently acting
        action_queue: Queue of pending actions
        log: Battle event log
    """
    team_a: list[Robot] = field(default_factory=list)
    team_b: list[Robot] = field(default_factory=list)
    turn_count: int = 0
    phase: BattlePhase = BattlePhase.SETUP
    current_actor: Robot | None = None
    action_queue: list[Action] = field(default_factory=list)
    log: BattleLog = field(default_factory=BattleLog)
    
    @property
    def all_robots(self) -> list[Robot]:
        """Get all robots in the battle."""
        return self.team_a + self.team_b
    
    @property
    def active_team_a(self) -> list[Robot]:
        """Get functional robots on team A."""
        return [r for r in self.team_a if r.is_functional]
    
    @property
    def active_team_b(self) -> list[Robot]:
        """Get functional robots on team B."""
        return [r for r in self.team_b if r.is_functional]
    
    @property
    def winner(self) -> int | None:
        """
        Get winning team if battle is over.
        
        Returns:
            0 for team A, 1 for team B, None if ongoing or not started
        """
        # Battle not started if no robots on either team
        if not self.team_a and not self.team_b:
            return None
        
        # Team A wins if team B has no functional robots
        if self.team_b and not self.active_team_b:
            return 0
        # Team B wins if team A has no functional robots
        if self.team_a and not self.active_team_a:
            return 1
        return None
    
    @property
    def is_over(self) -> bool:
        """Check if battle has ended."""
        return self.winner is not None
    
    def get_enemies(self, robot: Robot) -> list[Robot]:
        """Get enemy robots for a given robot."""
        if robot.team == 0:
            return self.active_team_b
        return self.active_team_a
    
    def get_allies(self, robot: Robot) -> list[Robot]:
        """Get allied robots for a given robot (including self)."""
        if robot.team == 0:
            return self.active_team_a
        return self.active_team_b
    
    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "team_a": [r.to_dict() for r in self.team_a],
            "team_b": [r.to_dict() for r in self.team_b],
            "turn_count": self.turn_count,
            "phase": self.phase.name,
            "current_actor": self.current_actor.name if self.current_actor else None,
        }


class Strategy(ABC):
    """Abstract base class for AI strategies."""
    
    @abstractmethod
    def select_action(
        self,
        robot: Robot,
        state: BattleState,
    ) -> Action | None:
        """
        Select an action for the robot to perform.
        
        Args:
            robot: The robot selecting an action
            state: Current battle state
            
        Returns:
            Selected action or None if no action available
        """
        pass
    
    def _get_usable_parts(self, robot: Robot) -> list[Part]:
        """Get parts that can perform actions."""
        return [p for p in robot.parts if p.can_act]
    
    def _select_random_target(
        self,
        enemies: list[Robot],
    ) -> Robot | None:
        """Select a random enemy target."""
        if not enemies:
            return None
        return random.choice(enemies)


class RandomStrategy(Strategy):
    """Strategy that selects actions randomly."""
    
    def select_action(
        self,
        robot: Robot,
        state: BattleState,
    ) -> Action | None:
        """Select a random action."""
        usable_parts = self._get_usable_parts(robot)
        if not usable_parts:
            return None
        
        part = random.choice(usable_parts)
        
        # Determine target based on action type
        if part.action_type in (ActionType.SUPPORT, ActionType.DEFEND):
            targets = state.get_allies(robot)
        else:
            targets = state.get_enemies(robot)
        
        target = self._select_random_target(targets)
        if not target:
            return None
        
        # Random target part
        target_part = random.choice(list(PartType))
        
        return Action(
            actor=robot,
            part=part,
            target=target,
            target_part=target_part,
        )


class AggressiveStrategy(Strategy):
    """Strategy that prioritizes attack actions and targets heads."""
    
    def select_action(
        self,
        robot: Robot,
        state: BattleState,
    ) -> Action | None:
        """Select most aggressive action available."""
        usable_parts = self._get_usable_parts(robot)
        if not usable_parts:
            return None
        
        # Prioritize attack actions
        attack_parts = [
            p for p in usable_parts
            if p.action_type in (ActionType.SHOOT, ActionType.STRIKE)
        ]
        
        if attack_parts:
            # Choose highest power attack
            part = max(attack_parts, key=lambda p: p.power)
        else:
            # Fall back to any action
            part = random.choice(usable_parts)
        
        enemies = state.get_enemies(robot)
        if not enemies:
            return None
        
        # Target enemy with lowest head armor
        target = min(enemies, key=lambda r: r.head.armor)
        
        # Always target head for maximum impact
        target_part = PartType.HEAD
        
        return Action(
            actor=robot,
            part=part,
            target=target,
            target_part=target_part,
        )


class DefensiveStrategy(Strategy):
    """Strategy that prioritizes support and disruption."""
    
    def select_action(
        self,
        robot: Robot,
        state: BattleState,
    ) -> Action | None:
        """Select defensive/supportive action."""
        usable_parts = self._get_usable_parts(robot)
        if not usable_parts:
            return None
        
        # Prioritize support/disrupt actions
        support_parts = [
            p for p in usable_parts
            if p.action_type in (ActionType.SUPPORT, ActionType.DEFEND, ActionType.DISRUPT)
        ]
        
        if support_parts:
            part = random.choice(support_parts)
        else:
            # Fall back to weakest attack
            attack_parts = [
                p for p in usable_parts
                if p.action_type in (ActionType.SHOOT, ActionType.STRIKE)
            ]
            if attack_parts:
                part = min(attack_parts, key=lambda p: p.power)
            else:
                part = random.choice(usable_parts)
        
        # Determine target based on action type
        if part.action_type in (ActionType.SUPPORT, ActionType.DEFEND):
            allies = state.get_allies(robot)
            # Support ally with lowest total armor
            target = min(allies, key=lambda r: r.total_armor)
            target_part = None
        else:
            enemies = state.get_enemies(robot)
            if not enemies:
                return None
            # Target enemy arms to reduce their attack capability
            target = random.choice(enemies)
            target_part = random.choice([PartType.RIGHT_ARM, PartType.LEFT_ARM])
        
        return Action(
            actor=robot,
            part=part,
            target=target,
            target_part=target_part,
        )


class MedalBasedStrategy(Strategy):
    """Strategy that uses the robot's medal weights for action selection."""
    
    def select_action(
        self,
        robot: Robot,
        state: BattleState,
    ) -> Action | None:
        """Select action based on medal personality weights."""
        usable_parts = self._get_usable_parts(robot)
        if not usable_parts:
            return None
        
        # Weight parts by medal preference
        weights = [robot.medal.get_weight(p.action_type) for p in usable_parts]
        total_weight = sum(weights)
        
        if total_weight == 0:
            part = random.choice(usable_parts)
        else:
            # Weighted random selection
            r = random.random() * total_weight
            cumulative = 0.0
            part = usable_parts[0]
            for p, w in zip(usable_parts, weights):
                cumulative += w
                if r <= cumulative:
                    part = p
                    break
        
        # Determine target
        if part.action_type in (ActionType.SUPPORT, ActionType.DEFEND):
            targets = state.get_allies(robot)
        else:
            targets = state.get_enemies(robot)
        
        if not targets:
            return None
        
        target = random.choice(targets)
        target_part = random.choice(list(PartType))
        
        return Action(
            actor=robot,
            part=part,
            target=target,
            target_part=target_part,
        )


class BattleManager:
    """
    Manages battle execution and turn progression.
    
    This class coordinates between:
    - Python battle logic (turn order, action selection)
    - C++ engine (damage calculation, ATB updates)
    """
    
    def __init__(
        self,
        state: BattleState,
        player_strategy: Strategy | None = None,
        enemy_strategy: Strategy | None = None,
    ):
        """
        Initialize battle manager.
        
        Args:
            state: Initial battle state
            player_strategy: Strategy for player team (None for manual)
            enemy_strategy: Strategy for enemy team
        """
        self.state = state
        self.player_strategy = player_strategy
        self.enemy_strategy = enemy_strategy or AggressiveStrategy()
        self._use_cpp_engine = False
        
        # Try to import C++ engine
        try:
            from ..engine import battle_engine
            self._engine = battle_engine
            self._use_cpp_engine = True
        except ImportError:
            self._engine = None
    
    def start_battle(self) -> None:
        """Initialize and start the battle."""
        self.state.phase = BattlePhase.IN_PROGRESS
        self.state.turn_count = 1
        self.state.log.add_message("Battle started!")
        
        # Initialize ATB gauges
        for robot in self.state.all_robots:
            robot.atb_gauge = random.uniform(0, 30)
    
    def get_next_actor(self) -> Robot | None:
        """
        Determine which robot acts next based on ATB.
        
        Returns:
            Robot with highest ATB gauge >= 100, or None
        """
        ready_robots = [
            r for r in self.state.all_robots
            if r.is_functional and r.atb_gauge >= 100
        ]
        
        if not ready_robots:
            return None
        
        # Highest ATB goes first
        return max(ready_robots, key=lambda r: r.atb_gauge)
    
    def advance_time(self, delta: float = 10.0) -> None:
        """
        Advance ATB gauges for all robots.
        
        Args:
            delta: Base time units to advance
        """
        if self._use_cpp_engine and self._engine:
            # Use C++ engine for ATB update
            state_dict = self.state.to_dict()
            new_state = self._engine.update_atb(state_dict, delta)
            self._apply_atb_update(new_state)
        else:
            # Python fallback
            for robot in self.state.all_robots:
                if robot.is_functional:
                    # ATB speed based on legs charge stat
                    speed = 100.0 / max(robot.legs.charge, 1)
                    robot.atb_gauge += delta * speed
    
    def _apply_atb_update(self, new_state: dict[str, Any]) -> None:
        """Apply ATB updates from C++ engine."""
        for robot_data in new_state.get("robots", []):
            for robot in self.state.all_robots:
                if robot.name == robot_data["name"]:
                    robot.atb_gauge = robot_data["atb_gauge"]
    
    def execute_action(self, action: Action) -> ActionResult:
        """
        Execute an action and apply results.
        
        Args:
            action: Action to execute
            
        Returns:
            Result of the action
        """
        # Reset actor's ATB
        action.actor.atb_gauge = 0
        
        if self._use_cpp_engine and self._engine:
            # Use C++ engine for calculation
            result_dict = self._engine.simulate_action(action.to_dict())
            result = self._create_result_from_dict(action, result_dict)
        else:
            # Python fallback calculation
            result = self._calculate_action_result(action)
        
        # Apply result to state
        self._apply_result(result)
        
        # Log the action
        self.state.log.add_action_result(result)
        
        return result
    
    def _calculate_action_result(self, action: Action) -> ActionResult:
        """
        Calculate action result using Python (fallback).
        
        Args:
            action: Action to calculate
            
        Returns:
            Calculated result
        """
        from .rules import BattleRules
        
        # Calculate hit
        hit_chance = BattleRules.calculate_hit_chance(
            action.part.success_value + action.part.hit_bonus,
            action.target.total_evade,
        )
        
        hit = random.random() * 100 < hit_chance
        
        damage = 0
        effect = ""
        
        if action.part.action_type in (ActionType.SHOOT, ActionType.STRIKE):
            if hit:
                damage = BattleRules.calculate_damage(
                    action.part.power,
                    random.uniform(0.8, 1.2),
                )
                effect = "Hit!"
            else:
                effect = "Miss!"
        elif action.part.action_type == ActionType.SUPPORT:
            if hit:
                damage = -BattleRules.calculate_damage(action.part.power, 0.5)
                effect = "Healed!"
            else:
                effect = "Failed!"
        elif action.part.action_type == ActionType.DISRUPT:
            if hit:
                effect = "Disrupted!"
            else:
                effect = "Resisted!"
        
        return ActionResult(
            action=action,
            hit=hit,
            damage=damage,
            effect=effect,
        )
    
    def _create_result_from_dict(
        self,
        action: Action,
        result_dict: dict[str, Any],
    ) -> ActionResult:
        """Create ActionResult from C++ engine response."""
        return ActionResult(
            action=action,
            hit=result_dict.get("hit", False),
            damage=result_dict.get("damage", 0),
            effect=result_dict.get("effect", ""),
        )
    
    def _apply_result(self, result: ActionResult) -> None:
        """Apply action result to battle state."""
        if result.damage > 0:
            # Apply damage to target part
            target_part_type = result.action.target_part or PartType.HEAD
            target_part = result.action.target.get_part_by_type(target_part_type)
            target_part.take_damage(result.damage)
        elif result.damage < 0:
            # Healing
            target_part_type = result.action.target_part or PartType.HEAD
            target_part = result.action.target.get_part_by_type(target_part_type)
            target_part.armor = min(
                target_part.armor - result.damage,
                100,  # Max armor cap
            )
    
    def run_turn(self) -> ActionResult | None:
        """
        Run a single turn of combat.
        
        Returns:
            Result of the action taken, or None if no action
        """
        # Check if battle is over
        if self.state.is_over:
            self.state.phase = BattlePhase.FINISHED
            winner = "Player" if self.state.winner == 0 else "Enemy"
            self.state.log.add_message(f"{winner} wins!")
            return None
        
        # Get next actor
        actor = self.get_next_actor()
        
        if actor is None:
            # Advance time until someone is ready
            self.advance_time()
            return None
        
        self.state.current_actor = actor
        
        # Select action based on team
        if actor.team == 0:
            self.state.phase = BattlePhase.PLAYER_TURN
            if self.player_strategy:
                action = self.player_strategy.select_action(actor, self.state)
            else:
                # Manual mode - return None to wait for player input
                return None
        else:
            self.state.phase = BattlePhase.ENEMY_TURN
            action = self.enemy_strategy.select_action(actor, self.state)
        
        if action is None:
            # Skip turn if no valid action
            actor.atb_gauge = 0
            return None
        
        # Execute action
        result = self.execute_action(action)
        
        # Increment turn counter
        self.state.turn_count += 1
        
        return result
    
    def run_until_complete(self, max_turns: int = 1000) -> int | None:
        """
        Run battle until completion.
        
        Args:
            max_turns: Maximum turns before forced draw
            
        Returns:
            Winning team (0 or 1) or None for draw
        """
        while not self.state.is_over and self.state.turn_count < max_turns:
            self.run_turn()
        
        return self.state.winner
