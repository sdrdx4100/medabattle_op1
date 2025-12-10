"""
Engine module for C++ battle processing bindings.

This module provides Python bindings to the C++ battle core
for high-performance damage calculations and ATB updates.
"""

# Try to import the compiled C++ module
try:
    from .battle_engine import simulate_action, update_atb
    HAS_CPP_ENGINE = True
except ImportError:
    # C++ module not available, provide Python fallback stubs
    HAS_CPP_ENGINE = False
    
    def simulate_action(action_dict: dict) -> dict:
        """
        Simulate a single action (Python fallback).
        
        This is a stub that should be replaced by the C++ implementation.
        The actual calculation is done in battle_logic.py when C++ is unavailable.
        """
        raise NotImplementedError(
            "C++ engine not available. "
            "Build the engine or use Python fallback in BattleManager."
        )
    
    def update_atb(state_dict: dict, delta: float) -> dict:
        """
        Update ATB gauges for all robots (Python fallback).
        
        This is a stub that should be replaced by the C++ implementation.
        The actual calculation is done in battle_logic.py when C++ is unavailable.
        """
        raise NotImplementedError(
            "C++ engine not available. "
            "Build the engine or use Python fallback in BattleManager."
        )


__all__ = ["simulate_action", "update_atb", "HAS_CPP_ENGINE"]
