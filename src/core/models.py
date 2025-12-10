"""
Data models for Medabot-style robot battle simulation.

This module defines the core data structures for:
- Parts (Head, Arms, Legs)
- Medals (AI personality)
- Robots (assembled units)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any

import yaml


class PartType(Enum):
    """Types of robot parts."""
    HEAD = auto()
    RIGHT_ARM = auto()
    LEFT_ARM = auto()
    LEGS = auto()


class ActionType(Enum):
    """Types of actions that parts can perform."""
    SHOOT = auto()      # Ranged attack
    STRIKE = auto()     # Melee attack
    SUPPORT = auto()    # Healing/buff
    DISRUPT = auto()    # Debuff/status effect
    DEFEND = auto()     # Defensive action
    NONE = auto()       # No action (e.g., legs)


@dataclass
class Part:
    """
    Represents a robot part with stats and action capability.
    
    Attributes:
        name: Display name of the part
        part_type: Type of part (HEAD, RIGHT_ARM, etc.)
        action_type: Type of action this part performs
        success_value: Base accuracy/success rate
        power: Base damage/effect power
        charge: Speed to ready action (lower = faster)
        cooldown: Recovery time after action (lower = faster)
        armor: Part's durability (HP)
        hit_bonus: Additional accuracy modifier
        evade_bonus: Additional evasion modifier
    """
    name: str
    part_type: PartType
    action_type: ActionType = ActionType.NONE
    success_value: int = 50
    power: int = 30
    charge: int = 20
    cooldown: int = 20
    armor: int = 30
    hit_bonus: int = 0
    evade_bonus: int = 0
    
    @property
    def is_destroyed(self) -> bool:
        """Check if part is destroyed (armor <= 0)."""
        return self.armor <= 0
    
    @property
    def can_act(self) -> bool:
        """Check if part can perform actions."""
        return not self.is_destroyed and self.action_type != ActionType.NONE
    
    def take_damage(self, damage: int) -> int:
        """
        Apply damage to this part.
        
        Args:
            damage: Amount of damage to apply
            
        Returns:
            Actual damage dealt (capped at remaining armor)
        """
        actual_damage = min(damage, self.armor)
        self.armor -= actual_damage
        return actual_damage
    
    def to_dict(self) -> dict[str, Any]:
        """Convert part to dictionary for serialization."""
        return {
            "name": self.name,
            "part_type": self.part_type.name,
            "action_type": self.action_type.name,
            "success_value": self.success_value,
            "power": self.power,
            "charge": self.charge,
            "cooldown": self.cooldown,
            "armor": self.armor,
            "hit_bonus": self.hit_bonus,
            "evade_bonus": self.evade_bonus,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Part:
        """Create Part from dictionary."""
        return cls(
            name=data["name"],
            part_type=PartType[data["part_type"]],
            action_type=ActionType[data.get("action_type", "NONE")],
            success_value=data.get("success_value", 50),
            power=data.get("power", 30),
            charge=data.get("charge", 20),
            cooldown=data.get("cooldown", 20),
            armor=data.get("armor", 30),
            hit_bonus=data.get("hit_bonus", 0),
            evade_bonus=data.get("evade_bonus", 0),
        )


@dataclass
class Medal:
    """
    Represents the AI personality/medal of a robot.
    
    The medal influences action selection through weighted preferences.
    
    Attributes:
        name: Medal name
        personality: Personality type description
        weights: Action type preferences (higher = more likely)
    """
    name: str
    personality: str = "Balanced"
    weights: dict[str, float] = field(default_factory=lambda: {
        "attack": 1.0,
        "support": 1.0,
        "disrupt": 1.0,
        "defend": 1.0,
    })
    
    def get_weight(self, action_type: ActionType) -> float:
        """Get weight for a given action type."""
        mapping = {
            ActionType.SHOOT: "attack",
            ActionType.STRIKE: "attack",
            ActionType.SUPPORT: "support",
            ActionType.DISRUPT: "disrupt",
            ActionType.DEFEND: "defend",
        }
        key = mapping.get(action_type, "attack")
        return self.weights.get(key, 1.0)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert medal to dictionary."""
        return {
            "name": self.name,
            "personality": self.personality,
            "weights": self.weights.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Medal:
        """Create Medal from dictionary."""
        return cls(
            name=data["name"],
            personality=data.get("personality", "Balanced"),
            weights=data.get("weights", {}),
        )


@dataclass
class Robot:
    """
    Represents an assembled robot unit.
    
    Attributes:
        name: Robot name
        head: Head part
        right_arm: Right arm part
        left_arm: Left arm part
        legs: Leg part
        medal: AI personality medal
        team: Team identifier (0 = player, 1 = enemy)
        position: Grid position (x, y)
        atb_gauge: Current ATB charge (0-100)
    """
    name: str
    head: Part
    right_arm: Part
    left_arm: Part
    legs: Part
    medal: Medal
    team: int = 0
    position: tuple[int, int] = (0, 0)
    atb_gauge: float = 0.0
    
    @property
    def parts(self) -> list[Part]:
        """Get all parts as a list."""
        return [self.head, self.right_arm, self.left_arm, self.legs]
    
    @property
    def is_functional(self) -> bool:
        """Check if robot can still function (head not destroyed)."""
        return not self.head.is_destroyed
    
    @property
    def available_actions(self) -> list[Part]:
        """Get parts that can perform actions."""
        return [p for p in self.parts if p.can_act]
    
    @property
    def total_armor(self) -> int:
        """Get total remaining armor across all parts."""
        return sum(p.armor for p in self.parts)
    
    @property
    def total_evade(self) -> int:
        """Get total evasion bonus from all parts."""
        return sum(p.evade_bonus for p in self.parts if not p.is_destroyed)
    
    def get_part_by_type(self, part_type: PartType) -> Part:
        """Get a specific part by type."""
        mapping = {
            PartType.HEAD: self.head,
            PartType.RIGHT_ARM: self.right_arm,
            PartType.LEFT_ARM: self.left_arm,
            PartType.LEGS: self.legs,
        }
        return mapping[part_type]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert robot to dictionary for serialization."""
        return {
            "name": self.name,
            "head": self.head.to_dict(),
            "right_arm": self.right_arm.to_dict(),
            "left_arm": self.left_arm.to_dict(),
            "legs": self.legs.to_dict(),
            "medal": self.medal.to_dict(),
            "team": self.team,
            "position": list(self.position),
            "atb_gauge": self.atb_gauge,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Robot:
        """Create Robot from dictionary."""
        return cls(
            name=data["name"],
            head=Part.from_dict(data["head"]),
            right_arm=Part.from_dict(data["right_arm"]),
            left_arm=Part.from_dict(data["left_arm"]),
            legs=Part.from_dict(data["legs"]),
            medal=Medal.from_dict(data["medal"]),
            team=data.get("team", 0),
            position=tuple(data.get("position", [0, 0])),
            atb_gauge=data.get("atb_gauge", 0.0),
        )


def load_parts_from_yaml(path: Path | str) -> dict[str, Part]:
    """
    Load part definitions from a YAML file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Dictionary mapping part names to Part objects
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    parts = {}
    for part_data in data.get("parts", []):
        part = Part.from_dict(part_data)
        parts[part.name] = part
    return parts


def load_medals_from_yaml(path: Path | str) -> dict[str, Medal]:
    """
    Load medal definitions from a YAML file.
    
    Args:
        path: Path to the YAML file
        
    Returns:
        Dictionary mapping medal names to Medal objects
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    medals = {}
    for medal_data in data.get("medals", []):
        medal = Medal.from_dict(medal_data)
        medals[medal.name] = medal
    return medals


def create_sample_robot(name: str, team: int = 0) -> Robot:
    """
    Create a sample robot with default parts for testing.
    
    Args:
        name: Robot name
        team: Team identifier
        
    Returns:
        A fully assembled Robot
    """
    return Robot(
        name=name,
        head=Part(
            name="Standard Head",
            part_type=PartType.HEAD,
            action_type=ActionType.SUPPORT,
            success_value=60,
            power=20,
            charge=15,
            cooldown=25,
            armor=30,
        ),
        right_arm=Part(
            name="Blaster Arm",
            part_type=PartType.RIGHT_ARM,
            action_type=ActionType.SHOOT,
            success_value=55,
            power=40,
            charge=20,
            cooldown=30,
            armor=25,
        ),
        left_arm=Part(
            name="Sword Arm",
            part_type=PartType.LEFT_ARM,
            action_type=ActionType.STRIKE,
            success_value=50,
            power=50,
            charge=25,
            cooldown=25,
            armor=25,
        ),
        legs=Part(
            name="Standard Legs",
            part_type=PartType.LEGS,
            action_type=ActionType.NONE,
            armor=35,
            evade_bonus=10,
        ),
        medal=Medal(
            name="Balanced Medal",
            personality="Balanced",
        ),
        team=team,
    )
