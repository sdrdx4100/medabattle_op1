"""
Tests for core data models.
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.core.models import (
    Part,
    PartType,
    ActionType,
    Medal,
    Robot,
    create_sample_robot,
    load_parts_from_yaml,
    load_medals_from_yaml,
)


class TestPart:
    """Tests for the Part class."""
    
    def test_create_part(self):
        """Test basic part creation."""
        part = Part(
            name="Test Blaster",
            part_type=PartType.RIGHT_ARM,
            action_type=ActionType.SHOOT,
            success_value=55,
            power=40,
            charge=20,
            cooldown=30,
            armor=25,
        )
        
        assert part.name == "Test Blaster"
        assert part.part_type == PartType.RIGHT_ARM
        assert part.action_type == ActionType.SHOOT
        assert part.armor == 25
        assert not part.is_destroyed
        assert part.can_act
    
    def test_part_destruction(self):
        """Test part destruction mechanics."""
        part = Part(
            name="Test Part",
            part_type=PartType.HEAD,
            action_type=ActionType.SUPPORT,
            armor=30,
        )
        
        # Take partial damage
        damage = part.take_damage(10)
        assert damage == 10
        assert part.armor == 20
        assert not part.is_destroyed
        
        # Take more damage than remaining armor
        damage = part.take_damage(50)
        assert damage == 20  # Capped at remaining armor
        assert part.armor == 0
        assert part.is_destroyed
        assert not part.can_act
    
    def test_part_serialization(self):
        """Test part to/from dict conversion."""
        part = Part(
            name="Serialization Test",
            part_type=PartType.LEFT_ARM,
            action_type=ActionType.STRIKE,
            success_value=50,
            power=45,
            charge=25,
            cooldown=25,
            armor=30,
            hit_bonus=5,
            evade_bonus=0,
        )
        
        # Convert to dict
        data = part.to_dict()
        assert data["name"] == "Serialization Test"
        assert data["part_type"] == "LEFT_ARM"
        assert data["action_type"] == "STRIKE"
        
        # Convert back
        restored = Part.from_dict(data)
        assert restored.name == part.name
        assert restored.part_type == part.part_type
        assert restored.power == part.power
    
    def test_legs_cannot_act(self):
        """Test that legs with NONE action type cannot act."""
        legs = Part(
            name="Standard Legs",
            part_type=PartType.LEGS,
            action_type=ActionType.NONE,
            armor=35,
        )
        
        assert not legs.can_act


class TestMedal:
    """Tests for the Medal class."""
    
    def test_create_medal(self):
        """Test basic medal creation."""
        medal = Medal(
            name="Aggressive Medal",
            personality="Aggressive",
            weights={
                "attack": 2.0,
                "support": 0.5,
                "disrupt": 0.8,
                "defend": 0.3,
            },
        )
        
        assert medal.name == "Aggressive Medal"
        assert medal.personality == "Aggressive"
        assert medal.weights["attack"] == 2.0
    
    def test_get_weight(self):
        """Test weight lookup for action types."""
        medal = Medal(
            name="Test Medal",
            weights={
                "attack": 2.0,
                "support": 1.5,
                "disrupt": 1.0,
                "defend": 0.5,
            },
        )
        
        assert medal.get_weight(ActionType.SHOOT) == 2.0
        assert medal.get_weight(ActionType.STRIKE) == 2.0
        assert medal.get_weight(ActionType.SUPPORT) == 1.5
        assert medal.get_weight(ActionType.DISRUPT) == 1.0
        assert medal.get_weight(ActionType.DEFEND) == 0.5
    
    def test_medal_serialization(self):
        """Test medal to/from dict conversion."""
        medal = Medal(
            name="Test Medal",
            personality="Tactical",
            weights={"attack": 1.0, "support": 1.2},
        )
        
        data = medal.to_dict()
        restored = Medal.from_dict(data)
        
        assert restored.name == medal.name
        assert restored.personality == medal.personality


class TestRobot:
    """Tests for the Robot class."""
    
    def test_create_sample_robot(self):
        """Test sample robot creation."""
        robot = create_sample_robot("TestBot", team=0)
        
        assert robot.name == "TestBot"
        assert robot.team == 0
        assert robot.is_functional
        assert len(robot.parts) == 4
        assert robot.head is not None
        assert robot.right_arm is not None
        assert robot.left_arm is not None
        assert robot.legs is not None
    
    def test_robot_functionality(self):
        """Test robot functionality based on head state."""
        robot = create_sample_robot("FunctionalTest")
        
        assert robot.is_functional
        
        # Destroy head
        robot.head.armor = 0
        assert not robot.is_functional
    
    def test_available_actions(self):
        """Test getting available actions."""
        robot = create_sample_robot("ActionTest")
        
        actions = robot.available_actions
        assert len(actions) >= 2  # At least head and arms can act
        
        # Destroy an arm
        robot.right_arm.armor = 0
        actions_after = robot.available_actions
        assert len(actions_after) == len(actions) - 1
    
    def test_total_armor(self):
        """Test total armor calculation."""
        robot = create_sample_robot("ArmorTest")
        
        initial_armor = robot.total_armor
        assert initial_armor > 0
        
        # Damage a part
        robot.head.take_damage(10)
        assert robot.total_armor == initial_armor - 10
    
    def test_robot_serialization(self):
        """Test robot to/from dict conversion."""
        robot = create_sample_robot("SerializeBot", team=1)
        robot.position = (5, 3)
        robot.atb_gauge = 75.5
        
        data = robot.to_dict()
        restored = Robot.from_dict(data)
        
        assert restored.name == robot.name
        assert restored.team == robot.team
        assert restored.position == robot.position
        assert restored.atb_gauge == robot.atb_gauge
        assert restored.head.name == robot.head.name
    
    def test_get_part_by_type(self):
        """Test getting parts by type."""
        robot = create_sample_robot("PartTypeTest")
        
        head = robot.get_part_by_type(PartType.HEAD)
        assert head == robot.head
        
        legs = robot.get_part_by_type(PartType.LEGS)
        assert legs == robot.legs


class TestYAMLLoading:
    """Tests for YAML data loading."""
    
    def test_load_parts_from_yaml(self):
        """Test loading parts from YAML file."""
        yaml_content = {
            "parts": [
                {
                    "name": "Test Head",
                    "part_type": "HEAD",
                    "action_type": "SUPPORT",
                    "success_value": 60,
                    "power": 20,
                    "charge": 15,
                    "cooldown": 25,
                    "armor": 30,
                },
                {
                    "name": "Test Arm",
                    "part_type": "RIGHT_ARM",
                    "action_type": "SHOOT",
                    "power": 40,
                    "armor": 25,
                },
            ]
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
        ) as f:
            yaml.dump(yaml_content, f)
            temp_path = Path(f.name)
        
        try:
            parts = load_parts_from_yaml(temp_path)
            assert "Test Head" in parts
            assert "Test Arm" in parts
            assert parts["Test Head"].part_type == PartType.HEAD
            assert parts["Test Arm"].power == 40
        finally:
            temp_path.unlink()
    
    def test_load_medals_from_yaml(self):
        """Test loading medals from YAML file."""
        yaml_content = {
            "medals": [
                {
                    "name": "Balanced Medal",
                    "personality": "Balanced",
                    "weights": {
                        "attack": 1.0,
                        "support": 1.0,
                    },
                },
                {
                    "name": "Aggressive Medal",
                    "personality": "Aggressive",
                    "weights": {
                        "attack": 2.0,
                        "support": 0.5,
                    },
                },
            ]
        }
        
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".yaml",
            delete=False,
        ) as f:
            yaml.dump(yaml_content, f)
            temp_path = Path(f.name)
        
        try:
            medals = load_medals_from_yaml(temp_path)
            assert "Balanced Medal" in medals
            assert "Aggressive Medal" in medals
            assert medals["Aggressive Medal"].weights["attack"] == 2.0
        finally:
            temp_path.unlink()
