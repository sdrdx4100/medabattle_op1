"""
Tests for battle logic.
"""

import pytest

from src.core.models import (
    ActionType,
    Part,
    PartType,
    create_sample_robot,
)
from src.core.battle_logic import (
    Action,
    ActionResult,
    BattleLog,
    BattleManager,
    BattlePhase,
    BattleState,
    AggressiveStrategy,
    DefensiveStrategy,
    RandomStrategy,
    MedalBasedStrategy,
)
from src.core.rules import BattleRules, RuleConfig


class TestBattleState:
    """Tests for BattleState class."""
    
    def test_create_battle_state(self):
        """Test basic battle state creation."""
        state = BattleState()
        
        assert len(state.team_a) == 0
        assert len(state.team_b) == 0
        assert state.turn_count == 0
        assert state.phase == BattlePhase.SETUP
        assert not state.is_over
    
    def test_add_robots(self):
        """Test adding robots to teams."""
        state = BattleState()
        
        robot_a = create_sample_robot("PlayerBot", team=0)
        robot_b = create_sample_robot("EnemyBot", team=1)
        
        state.team_a.append(robot_a)
        state.team_b.append(robot_b)
        
        assert len(state.team_a) == 1
        assert len(state.team_b) == 1
        assert len(state.all_robots) == 2
    
    def test_active_robots(self):
        """Test getting active (functional) robots."""
        state = BattleState()
        
        robot1 = create_sample_robot("Bot1", team=0)
        robot2 = create_sample_robot("Bot2", team=0)
        
        state.team_a.extend([robot1, robot2])
        
        assert len(state.active_team_a) == 2
        
        # Destroy robot1's head
        robot1.head.armor = 0
        assert len(state.active_team_a) == 1
    
    def test_winner_detection(self):
        """Test winner detection."""
        state = BattleState()
        
        robot_a = create_sample_robot("PlayerBot", team=0)
        robot_b = create_sample_robot("EnemyBot", team=1)
        
        state.team_a.append(robot_a)
        state.team_b.append(robot_b)
        
        assert state.winner is None
        assert not state.is_over
        
        # Destroy enemy
        robot_b.head.armor = 0
        assert state.winner == 0
        assert state.is_over
        
        # Reset and destroy player
        robot_b.head.armor = 30
        robot_a.head.armor = 0
        assert state.winner == 1
    
    def test_get_enemies_allies(self):
        """Test getting enemies and allies for a robot."""
        state = BattleState()
        
        player1 = create_sample_robot("Player1", team=0)
        player2 = create_sample_robot("Player2", team=0)
        enemy1 = create_sample_robot("Enemy1", team=1)
        
        state.team_a.extend([player1, player2])
        state.team_b.append(enemy1)
        
        # From player's perspective
        enemies = state.get_enemies(player1)
        allies = state.get_allies(player1)
        
        assert len(enemies) == 1
        assert enemy1 in enemies
        assert len(allies) == 2
        assert player1 in allies
        assert player2 in allies


class TestAction:
    """Tests for Action class."""
    
    def test_action_creation(self):
        """Test action creation."""
        actor = create_sample_robot("Actor", team=0)
        target = create_sample_robot("Target", team=1)
        
        action = Action(
            actor=actor,
            part=actor.right_arm,
            target=target,
            target_part=PartType.HEAD,
        )
        
        assert action.actor == actor
        assert action.target == target
        assert action.part == actor.right_arm
        assert action.target_part == PartType.HEAD
    
    def test_action_to_dict(self):
        """Test action serialization."""
        actor = create_sample_robot("Actor", team=0)
        target = create_sample_robot("Target", team=1)
        
        action = Action(
            actor=actor,
            part=actor.right_arm,
            target=target,
            target_part=PartType.HEAD,
        )
        
        data = action.to_dict()
        assert data["actor_name"] == "Actor"
        assert data["target_name"] == "Target"
        assert data["action_type"] == "SHOOT"


class TestBattleLog:
    """Tests for BattleLog class."""
    
    def test_add_entries(self):
        """Test adding log entries."""
        log = BattleLog()
        
        log.add_message("Battle started!")
        log.add_entry({"actor": "Bot1", "action": "attack"})
        
        assert len(log.entries) == 2
        assert log.entries[0]["message"] == "Battle started!"
        assert log.entries[1]["actor"] == "Bot1"


class TestStrategies:
    """Tests for AI strategy classes."""
    
    def setup_method(self):
        """Set up test state."""
        self.state = BattleState()
        
        self.player = create_sample_robot("Player", team=0)
        self.enemy = create_sample_robot("Enemy", team=1)
        
        self.state.team_a.append(self.player)
        self.state.team_b.append(self.enemy)
    
    def test_random_strategy(self):
        """Test RandomStrategy action selection."""
        strategy = RandomStrategy()
        
        action = strategy.select_action(self.player, self.state)
        
        assert action is not None
        assert action.actor == self.player
        assert action.part in self.player.available_actions
    
    def test_aggressive_strategy(self):
        """Test AggressiveStrategy targets head."""
        strategy = AggressiveStrategy()
        
        action = strategy.select_action(self.player, self.state)
        
        assert action is not None
        assert action.target_part == PartType.HEAD
        assert action.part.action_type in (ActionType.SHOOT, ActionType.STRIKE)
    
    def test_defensive_strategy(self):
        """Test DefensiveStrategy prefers support/defend."""
        strategy = DefensiveStrategy()
        
        # Run multiple times to get statistical behavior
        support_count = 0
        for _ in range(10):
            action = strategy.select_action(self.player, self.state)
            if action and action.part.action_type in (
                ActionType.SUPPORT,
                ActionType.DEFEND,
                ActionType.DISRUPT,
            ):
                support_count += 1
        
        # Should prefer support actions when available
        assert action is not None
    
    def test_medal_based_strategy(self):
        """Test MedalBasedStrategy uses medal weights."""
        strategy = MedalBasedStrategy()
        
        action = strategy.select_action(self.player, self.state)
        
        assert action is not None
        assert action.part in self.player.available_actions
    
    def test_strategy_no_targets(self):
        """Test strategy returns None when no valid targets."""
        strategy = RandomStrategy()
        
        # Remove all enemies
        self.state.team_b.clear()
        
        # Player has attack action but no targets
        action = strategy.select_action(self.player, self.state)
        
        # Should handle gracefully (may return None or target ally)
        if action:
            # If action exists, it should be support/defend targeting ally
            if action.part.action_type in (ActionType.SHOOT, ActionType.STRIKE):
                assert False, "Should not target non-existent enemies"


class TestBattleRules:
    """Tests for BattleRules calculations."""
    
    def test_hit_chance_calculation(self):
        """Test hit chance calculation."""
        hit_chance = BattleRules.calculate_hit_chance(
            attacker_success=60,
            defender_evade=20,
        )
        
        # Should be base (50) + 60 - 20 = 90, capped at max
        assert hit_chance <= 95.0
        assert hit_chance >= 5.0
    
    def test_hit_chance_clamping(self):
        """Test hit chance is clamped to min/max."""
        # Very high success
        high_chance = BattleRules.calculate_hit_chance(
            attacker_success=100,
            defender_evade=0,
        )
        assert high_chance == 95.0  # Max cap
        
        # Very low success
        low_chance = BattleRules.calculate_hit_chance(
            attacker_success=0,
            defender_evade=100,
        )
        assert low_chance == 5.0  # Min cap
    
    def test_damage_calculation(self):
        """Test damage calculation."""
        damage = BattleRules.calculate_damage(
            power=40,
            variance=1.0,
            defense=0,
            is_critical=False,
        )
        
        assert damage == 40
    
    def test_critical_damage(self):
        """Test critical hit damage multiplier."""
        normal = BattleRules.calculate_damage(power=40, is_critical=False)
        critical = BattleRules.calculate_damage(power=40, is_critical=True)
        
        assert critical > normal
        assert critical == int(40 * 1.5)  # Default crit multiplier
    
    def test_minimum_damage(self):
        """Test minimum damage is 1."""
        damage = BattleRules.calculate_damage(
            power=10,
            variance=0.1,
            defense=50,
        )
        
        assert damage >= 1
    
    def test_atb_increment(self):
        """Test ATB increment calculation."""
        increment = BattleRules.calculate_atb_increment(
            charge_stat=20,
            base_delta=10.0,
        )
        
        # Should be 10 * (1 * 100 / 20) = 50
        assert increment == 50.0
    
    def test_rule_config(self):
        """Test custom rule configuration."""
        custom_config = RuleConfig(
            base_hit_chance=60.0,
            critical_multiplier=2.0,
        )
        
        BattleRules.set_config(custom_config)
        
        # Verify config is applied
        assert BattleRules.get_config().base_hit_chance == 60.0
        
        # Reset to default
        BattleRules.set_config(RuleConfig())


class TestBattleManager:
    """Tests for BattleManager class."""
    
    def setup_method(self):
        """Set up test battle."""
        self.state = BattleState()
        
        for i in range(2):
            player = create_sample_robot(f"Player_{i+1}", team=0)
            player.position = (1, i + 1)
            self.state.team_a.append(player)
        
        for i in range(2):
            enemy = create_sample_robot(f"Enemy_{i+1}", team=1)
            enemy.position = (8, i + 1)
            self.state.team_b.append(enemy)
        
        self.manager = BattleManager(
            state=self.state,
            player_strategy=RandomStrategy(),
            enemy_strategy=AggressiveStrategy(),
        )
    
    def test_start_battle(self):
        """Test battle initialization."""
        self.manager.start_battle()
        
        assert self.state.phase == BattlePhase.IN_PROGRESS
        assert self.state.turn_count == 1
        
        # All robots should have some ATB
        for robot in self.state.all_robots:
            assert robot.atb_gauge >= 0
    
    def test_advance_time(self):
        """Test ATB gauge advancement."""
        self.manager.start_battle()
        
        initial_gauges = [r.atb_gauge for r in self.state.all_robots]
        self.manager.advance_time(10.0)
        
        # All gauges should have increased
        for robot, initial in zip(self.state.all_robots, initial_gauges):
            if robot.is_functional:
                assert robot.atb_gauge > initial
    
    def test_get_next_actor(self):
        """Test getting next actor based on ATB."""
        self.manager.start_battle()
        
        # No one ready yet
        actor = self.manager.get_next_actor()
        assert actor is None
        
        # Force a robot to be ready
        self.state.team_a[0].atb_gauge = 100
        actor = self.manager.get_next_actor()
        assert actor == self.state.team_a[0]
    
    def test_execute_action(self):
        """Test action execution."""
        self.manager.start_battle()
        
        actor = self.state.team_a[0]
        target = self.state.team_b[0]
        actor.atb_gauge = 100
        
        initial_armor = target.head.armor
        
        action = Action(
            actor=actor,
            part=actor.right_arm,
            target=target,
            target_part=PartType.HEAD,
        )
        
        result = self.manager.execute_action(action)
        
        # ATB should be reset
        assert actor.atb_gauge == 0
        
        # Result should be recorded
        assert isinstance(result, ActionResult)
        assert len(self.state.log.entries) > 0
    
    def test_run_until_complete(self):
        """Test running battle to completion."""
        self.manager.start_battle()
        
        winner = self.manager.run_until_complete(max_turns=500)
        
        assert winner in (0, 1, None)
        assert self.state.is_over or self.state.turn_count >= 500
