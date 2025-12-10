"""
Engine module for C++ battle processing bindings.

This module provides Python bindings to the C++ battle core
for high-performance damage calculations and ATB updates.

When the C++ engine is not compiled/available, the HAS_CPP_ENGINE flag
is set to False, and BattleManager will use Python fallback implementations
in battle_logic.py instead of these stubs.
"""

from typing import Any

# Try to import the compiled C++ module
try:
    from .battle_engine import simulate_action, update_atb
    HAS_CPP_ENGINE = True
except ImportError:
    # C++ module not available - BattleManager uses Python fallbacks
    HAS_CPP_ENGINE = False
    
    def simulate_action(action_dict: dict[str, Any]) -> dict[str, Any]:
        """
        Simulate a single action (stub - C++ not available).
        
        Note: This stub should never be called directly when HAS_CPP_ENGINE
        is False. The BattleManager checks HAS_CPP_ENGINE and uses its own
        Python implementation (_calculate_action_result) as fallback.
        
        Args:
            action_dict: Action parameters
            
        Returns:
            Action result dictionary
            
        Raises:
            NotImplementedError: Always, as this is a stub
        """
        raise NotImplementedError(
            "C++ engine not available. "
            "BattleManager should use Python fallback when HAS_CPP_ENGINE is False."
        )
    
    def update_atb(state_dict: dict[str, Any], delta: float) -> dict[str, Any]:
        """
        Update ATB gauges for all robots (stub - C++ not available).
        
        Note: This stub should never be called directly when HAS_CPP_ENGINE
        is False. The BattleManager checks HAS_CPP_ENGINE and uses its own
        Python implementation in advance_time() as fallback.
        
        Args:
            state_dict: Battle state dictionary
            delta: Time delta for ATB advancement
            
        Returns:
            Updated state dictionary
            
        Raises:
            NotImplementedError: Always, as this is a stub
        """
        raise NotImplementedError(
            "C++ engine not available. "
            "BattleManager should use Python fallback when HAS_CPP_ENGINE is False."
        )


__all__ = ["simulate_action", "update_atb", "HAS_CPP_ENGINE"]
