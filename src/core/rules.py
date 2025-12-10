"""
Battle rules and calculations for combat mechanics.

This module defines the formulas and parameters for:
- Hit/miss calculations
- Damage calculations
- ATB gauge mechanics
- Status effects
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RuleConfig:
    """
    Configuration for battle rules.
    
    Allows rules to be customized or overridden for balance testing.
    """
    # Hit calculation
    base_hit_chance: float = 50.0
    max_hit_chance: float = 95.0
    min_hit_chance: float = 5.0
    
    # Damage calculation
    damage_variance_min: float = 0.8
    damage_variance_max: float = 1.2
    critical_multiplier: float = 1.5
    critical_chance: float = 10.0
    
    # ATB settings
    atb_max: float = 100.0
    atb_base_speed: float = 1.0
    
    # Part destruction
    min_damage: int = 1
    
    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "base_hit_chance": self.base_hit_chance,
            "max_hit_chance": self.max_hit_chance,
            "min_hit_chance": self.min_hit_chance,
            "damage_variance_min": self.damage_variance_min,
            "damage_variance_max": self.damage_variance_max,
            "critical_multiplier": self.critical_multiplier,
            "critical_chance": self.critical_chance,
            "atb_max": self.atb_max,
            "atb_base_speed": self.atb_base_speed,
            "min_damage": self.min_damage,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleConfig:
        """Create config from dictionary."""
        return cls(
            base_hit_chance=data.get("base_hit_chance", 50.0),
            max_hit_chance=data.get("max_hit_chance", 95.0),
            min_hit_chance=data.get("min_hit_chance", 5.0),
            damage_variance_min=data.get("damage_variance_min", 0.8),
            damage_variance_max=data.get("damage_variance_max", 1.2),
            critical_multiplier=data.get("critical_multiplier", 1.5),
            critical_chance=data.get("critical_chance", 10.0),
            atb_max=data.get("atb_max", 100.0),
            atb_base_speed=data.get("atb_base_speed", 1.0),
            min_damage=data.get("min_damage", 1),
        )


class BattleRules:
    """
    Static methods for battle calculations.
    
    These methods can be called from Python or used as reference
    for the C++ implementation.
    """
    
    _config: RuleConfig = RuleConfig()
    
    @classmethod
    def set_config(cls, config: RuleConfig) -> None:
        """Set the rule configuration."""
        cls._config = config
    
    @classmethod
    def get_config(cls) -> RuleConfig:
        """Get the current rule configuration."""
        return cls._config
    
    @classmethod
    def calculate_hit_chance(
        cls,
        attacker_success: int,
        defender_evade: int,
        modifiers: list[int] | None = None,
    ) -> float:
        """
        Calculate hit chance for an attack.
        
        Formula: base + attacker_success - defender_evade + modifiers
        Clamped between min and max hit chance.
        
        Args:
            attacker_success: Attacker's success value
            defender_evade: Defender's evasion value
            modifiers: Optional list of additional modifiers
            
        Returns:
            Hit chance as a percentage (0-100)
        """
        config = cls._config
        
        total_mod = sum(modifiers) if modifiers else 0
        
        hit_chance = (
            config.base_hit_chance
            + attacker_success
            - defender_evade
            + total_mod
        )
        
        return max(
            config.min_hit_chance,
            min(config.max_hit_chance, hit_chance),
        )
    
    @classmethod
    def calculate_damage(
        cls,
        power: int,
        variance: float = 1.0,
        defense: int = 0,
        is_critical: bool = False,
    ) -> int:
        """
        Calculate damage for an attack.
        
        Formula: power * variance * crit_mult - defense
        
        Args:
            power: Base attack power
            variance: Random variance multiplier
            defense: Defender's defense value
            is_critical: Whether this is a critical hit
            
        Returns:
            Final damage value (minimum 1)
        """
        config = cls._config
        
        crit_mult = config.critical_multiplier if is_critical else 1.0
        
        damage = power * variance * crit_mult - defense
        
        return max(config.min_damage, int(damage))
    
    @classmethod
    def calculate_atb_increment(
        cls,
        charge_stat: int,
        base_delta: float,
    ) -> float:
        """
        Calculate ATB gauge increment.
        
        Formula: base_delta * (atb_base_speed * 100 / charge_stat)
        
        Args:
            charge_stat: Robot's charge/speed stat
            base_delta: Base time units passed
            
        Returns:
            ATB increment amount
        """
        config = cls._config
        
        if charge_stat <= 0:
            charge_stat = 1
        
        speed = config.atb_base_speed * 100.0 / charge_stat
        return base_delta * speed
    
    @classmethod
    def calculate_cooldown(
        cls,
        cooldown_stat: int,
        base_cooldown: float = 50.0,
    ) -> float:
        """
        Calculate ATB penalty after action (negative gauge).
        
        Args:
            cooldown_stat: Part's cooldown stat
            base_cooldown: Base cooldown amount
            
        Returns:
            Cooldown penalty (subtracted from ATB)
        """
        return base_cooldown * (cooldown_stat / 100.0)
    
    @classmethod
    def is_critical_hit(cls, roll: float) -> bool:
        """
        Determine if an attack is a critical hit.
        
        Args:
            roll: Random roll (0-100)
            
        Returns:
            True if critical hit
        """
        return roll < cls._config.critical_chance
    
    @classmethod
    def calculate_support_healing(
        cls,
        power: int,
        effectiveness: float = 1.0,
    ) -> int:
        """
        Calculate healing amount for support actions.
        
        Args:
            power: Support power stat
            effectiveness: Effectiveness multiplier
            
        Returns:
            Healing amount
        """
        return max(1, int(power * effectiveness * 0.5))


@dataclass
class StatusEffect:
    """
    Represents a status effect on a robot.
    
    Attributes:
        name: Effect name
        duration: Turns remaining
        hit_modifier: Modifier to hit chance
        evade_modifier: Modifier to evasion
        damage_modifier: Modifier to damage dealt
        atb_modifier: Modifier to ATB speed
    """
    name: str
    duration: int = 3
    hit_modifier: int = 0
    evade_modifier: int = 0
    damage_modifier: float = 1.0
    atb_modifier: float = 1.0
    
    def tick(self) -> bool:
        """
        Decrement duration by 1.
        
        Returns:
            True if effect is still active
        """
        self.duration -= 1
        return self.duration > 0


# Predefined status effects
COMMON_EFFECTS: dict[str, StatusEffect] = {
    "accuracy_up": StatusEffect(
        name="Accuracy Up",
        duration=3,
        hit_modifier=20,
    ),
    "accuracy_down": StatusEffect(
        name="Accuracy Down",
        duration=3,
        hit_modifier=-20,
    ),
    "evasion_up": StatusEffect(
        name="Evasion Up",
        duration=3,
        evade_modifier=20,
    ),
    "evasion_down": StatusEffect(
        name="Evasion Down",
        duration=3,
        evade_modifier=-20,
    ),
    "power_up": StatusEffect(
        name="Power Up",
        duration=3,
        damage_modifier=1.5,
    ),
    "power_down": StatusEffect(
        name="Power Down",
        duration=3,
        damage_modifier=0.5,
    ),
    "haste": StatusEffect(
        name="Haste",
        duration=3,
        atb_modifier=1.5,
    ),
    "slow": StatusEffect(
        name="Slow",
        duration=3,
        atb_modifier=0.5,
    ),
}
