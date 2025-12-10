"""
Pyxel-based UI for Medabot battle simulation.

This module provides a simple, playable interface using
symbol-based graphics (□, ■, etc.) for robot representation.
"""

from __future__ import annotations

import pyxel

from ..core.battle_logic import (
    Action,
    AggressiveStrategy,
    BattleManager,
    BattlePhase,
    BattleState,
    MedalBasedStrategy,
)
from ..core.models import ActionType, PartType, Robot, create_sample_robot
from .renderer import BattleRenderer


class GameState:
    """Enumeration of game states."""
    TITLE = 0
    BATTLE = 1
    ACTION_SELECT = 2
    TARGET_SELECT = 3
    RESULT = 4
    GAME_OVER = 5


class MedaBattleApp:
    """
    Main Pyxel application for the battle game.
    
    Controls:
        - Arrow keys: Navigate menus / Select targets
        - Z: Confirm selection
        - X: Cancel / Back
        - Space: Advance turn
        - R: Reset battle
        - Q: Quit
    """
    
    # Window dimensions
    WIDTH = 256
    HEIGHT = 192
    
    def __init__(self):
        """Initialize the application."""
        pyxel.init(
            self.WIDTH,
            self.HEIGHT,
            title="MedaBattle",
            fps=30,
        )
        
        self.renderer = BattleRenderer()
        self.game_state = GameState.TITLE
        self.battle_state: BattleState | None = None
        self.battle_manager: BattleManager | None = None
        
        # UI state
        self.cursor_index = 0
        self.selected_part_index = 0
        self.message_log: list[str] = []
        self.max_log_lines = 5
        
        # Animation state
        self.frame_count = 0
        self.animation_timer = 0
        
        pyxel.run(self.update, self.draw)
    
    def setup_battle(self) -> None:
        """Set up a new battle."""
        self.battle_state = BattleState()
        
        # Create player team
        for i in range(3):
            robot = create_sample_robot(f"Player_{i+1}", team=0)
            robot.position = (2, 2 + i * 2)
            self.battle_state.team_a.append(robot)
        
        # Create enemy team
        for i in range(3):
            robot = create_sample_robot(f"Enemy_{i+1}", team=1)
            robot.position = (7, 2 + i * 2)
            self.battle_state.team_b.append(robot)
        
        # Create battle manager (no player strategy = manual control)
        self.battle_manager = BattleManager(
            state=self.battle_state,
            player_strategy=None,  # Manual control
            enemy_strategy=AggressiveStrategy(),
        )
        
        self.battle_manager.start_battle()
        self.message_log = ["Battle started!"]
        self.game_state = GameState.BATTLE
    
    def update(self) -> None:
        """Update game state."""
        self.frame_count += 1
        
        # Global controls
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()
        
        if self.game_state == GameState.TITLE:
            self._update_title()
        elif self.game_state == GameState.BATTLE:
            self._update_battle()
        elif self.game_state == GameState.ACTION_SELECT:
            self._update_action_select()
        elif self.game_state == GameState.TARGET_SELECT:
            self._update_target_select()
        elif self.game_state == GameState.GAME_OVER:
            self._update_game_over()
    
    def _update_title(self) -> None:
        """Update title screen."""
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_SPACE):
            self.setup_battle()
    
    def _update_battle(self) -> None:
        """Update battle state."""
        if self.battle_state is None or self.battle_manager is None:
            return
        
        # Check for game over
        if self.battle_state.is_over:
            self.game_state = GameState.GAME_OVER
            winner = "Player" if self.battle_state.winner == 0 else "Enemy"
            self.message_log.append(f"{winner} wins!")
            return
        
        # Reset with R
        if pyxel.btnp(pyxel.KEY_R):
            self.setup_battle()
            return
        
        # Advance ATB with Space
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.battle_manager.advance_time()
            
            # Check if anyone is ready to act
            actor = self.battle_manager.get_next_actor()
            if actor:
                self.battle_state.current_actor = actor
                if actor.team == 0:
                    # Player's turn - go to action select
                    self.cursor_index = 0
                    self.game_state = GameState.ACTION_SELECT
                else:
                    # Enemy's turn - let AI act
                    result = self.battle_manager.run_turn()
                    if result:
                        msg = f"{actor.name} uses {result.action.part.name}! {result.effect}"
                        if result.damage > 0:
                            msg += f" ({result.damage} dmg)"
                        self._add_log(msg)
    
    def _update_action_select(self) -> None:
        """Update action selection state."""
        if self.battle_state is None or self.battle_state.current_actor is None:
            return
        
        actor = self.battle_state.current_actor
        available_parts = actor.available_actions
        
        if not available_parts:
            # No actions available, skip turn
            actor.atb_gauge = 0
            self.game_state = GameState.BATTLE
            return
        
        # Navigate with arrows
        if pyxel.btnp(pyxel.KEY_UP):
            self.cursor_index = max(0, self.cursor_index - 1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cursor_index = min(len(available_parts) - 1, self.cursor_index + 1)
        
        # Select with Z
        if pyxel.btnp(pyxel.KEY_Z):
            self.selected_part_index = self.cursor_index
            self.cursor_index = 0
            self.game_state = GameState.TARGET_SELECT
        
        # Cancel with X (skip turn)
        if pyxel.btnp(pyxel.KEY_X):
            actor.atb_gauge = 0
            self.game_state = GameState.BATTLE
    
    def _update_target_select(self) -> None:
        """Update target selection state."""
        if self.battle_state is None or self.battle_state.current_actor is None:
            return
        
        actor = self.battle_state.current_actor
        part = actor.available_actions[self.selected_part_index]
        
        # Get valid targets based on action type
        if part.action_type in (ActionType.SUPPORT, ActionType.DEFEND):
            targets = self.battle_state.get_allies(actor)
        else:
            targets = self.battle_state.get_enemies(actor)
        
        if not targets:
            self.game_state = GameState.ACTION_SELECT
            return
        
        # Navigate
        if pyxel.btnp(pyxel.KEY_UP):
            self.cursor_index = max(0, self.cursor_index - 1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.cursor_index = min(len(targets) - 1, self.cursor_index + 1)
        
        # Select with Z
        if pyxel.btnp(pyxel.KEY_Z):
            target = targets[self.cursor_index]
            
            # Create and execute action
            action = Action(
                actor=actor,
                part=part,
                target=target,
                target_part=PartType.HEAD,  # Default to head
            )
            
            if self.battle_manager:
                result = self.battle_manager.execute_action(action)
                msg = f"{actor.name} uses {part.name}! {result.effect}"
                if result.damage > 0:
                    msg += f" ({result.damage} dmg)"
                self._add_log(msg)
            
            self.game_state = GameState.BATTLE
        
        # Cancel with X
        if pyxel.btnp(pyxel.KEY_X):
            self.cursor_index = self.selected_part_index
            self.game_state = GameState.ACTION_SELECT
    
    def _update_game_over(self) -> None:
        """Update game over state."""
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_R):
            self.setup_battle()
        if pyxel.btnp(pyxel.KEY_X):
            self.game_state = GameState.TITLE
    
    def _add_log(self, message: str) -> None:
        """Add a message to the log."""
        self.message_log.append(message)
        if len(self.message_log) > self.max_log_lines:
            self.message_log.pop(0)
    
    def draw(self) -> None:
        """Draw the game."""
        pyxel.cls(0)  # Clear with black
        
        if self.game_state == GameState.TITLE:
            self._draw_title()
        elif self.game_state in (
            GameState.BATTLE,
            GameState.ACTION_SELECT,
            GameState.TARGET_SELECT,
        ):
            self._draw_battle()
        elif self.game_state == GameState.GAME_OVER:
            self._draw_game_over()
    
    def _draw_title(self) -> None:
        """Draw title screen."""
        # Title
        pyxel.text(80, 60, "MEDABATTLE", 7)
        pyxel.text(70, 80, "Robot Battle Sim", 6)
        
        # Blinking prompt
        if (self.frame_count // 30) % 2 == 0:
            pyxel.text(70, 120, "Press Z to Start", 7)
        
        # Controls
        pyxel.text(20, 160, "Controls: Arrow=Move Z=Select X=Cancel", 5)
        pyxel.text(20, 170, "Space=Advance R=Reset Q=Quit", 5)
    
    def _draw_battle(self) -> None:
        """Draw battle screen."""
        if self.battle_state is None:
            return
        
        # Draw battlefield grid
        self.renderer.draw_battlefield()
        
        # Draw all robots
        for robot in self.battle_state.all_robots:
            is_current = robot == self.battle_state.current_actor
            self.renderer.draw_robot(robot, is_current)
        
        # Draw UI panels
        self._draw_status_panel()
        self._draw_log_panel()
        
        # Draw action/target menus if applicable
        if self.game_state == GameState.ACTION_SELECT:
            self._draw_action_menu()
        elif self.game_state == GameState.TARGET_SELECT:
            self._draw_target_menu()
    
    def _draw_status_panel(self) -> None:
        """Draw status panel showing team health."""
        # Team A status (left side)
        y = 140
        pyxel.text(4, y, "=== PLAYER ===", 7)
        y += 8
        
        if self.battle_state:
            for robot in self.battle_state.team_a:
                color = 7 if robot.is_functional else 8
                hp = f"HP:{robot.total_armor}"
                pyxel.text(4, y, f"{robot.name}: {hp}", color)
                y += 8
        
        # Team B status (right side)
        y = 140
        pyxel.text(180, y, "=== ENEMY ===", 7)
        y += 8
        
        if self.battle_state:
            for robot in self.battle_state.team_b:
                color = 7 if robot.is_functional else 8
                hp = f"HP:{robot.total_armor}"
                pyxel.text(180, y, f"{robot.name}: {hp}", color)
                y += 8
    
    def _draw_log_panel(self) -> None:
        """Draw message log panel."""
        pyxel.rect(0, 0, self.WIDTH, 20, 1)
        
        y = 2
        for msg in self.message_log[-2:]:
            pyxel.text(4, y, msg[:60], 7)
            y += 8
    
    def _draw_action_menu(self) -> None:
        """Draw action selection menu."""
        if self.battle_state is None or self.battle_state.current_actor is None:
            return
        
        actor = self.battle_state.current_actor
        parts = actor.available_actions
        
        # Draw menu background
        menu_x = 80
        menu_y = 40
        menu_w = 100
        menu_h = len(parts) * 12 + 16
        
        pyxel.rect(menu_x, menu_y, menu_w, menu_h, 1)
        pyxel.rectb(menu_x, menu_y, menu_w, menu_h, 7)
        
        pyxel.text(menu_x + 4, menu_y + 4, "Select Action:", 7)
        
        for i, part in enumerate(parts):
            y = menu_y + 16 + i * 12
            color = 10 if i == self.cursor_index else 7
            prefix = ">" if i == self.cursor_index else " "
            pyxel.text(menu_x + 8, y, f"{prefix}{part.name}", color)
    
    def _draw_target_menu(self) -> None:
        """Draw target selection menu."""
        if self.battle_state is None or self.battle_state.current_actor is None:
            return
        
        actor = self.battle_state.current_actor
        part = actor.available_actions[self.selected_part_index]
        
        from ..core.models import ActionType
        if part.action_type in (ActionType.SUPPORT, ActionType.DEFEND):
            targets = self.battle_state.get_allies(actor)
        else:
            targets = self.battle_state.get_enemies(actor)
        
        # Draw menu background
        menu_x = 80
        menu_y = 40
        menu_w = 100
        menu_h = len(targets) * 12 + 16
        
        pyxel.rect(menu_x, menu_y, menu_w, menu_h, 1)
        pyxel.rectb(menu_x, menu_y, menu_w, menu_h, 7)
        
        pyxel.text(menu_x + 4, menu_y + 4, "Select Target:", 7)
        
        for i, target in enumerate(targets):
            y = menu_y + 16 + i * 12
            color = 10 if i == self.cursor_index else 7
            prefix = ">" if i == self.cursor_index else " "
            hp = f"(HP:{target.total_armor})"
            pyxel.text(menu_x + 8, y, f"{prefix}{target.name} {hp}", color)
    
    def _draw_game_over(self) -> None:
        """Draw game over screen."""
        # Dim background
        pyxel.rect(0, 0, self.WIDTH, self.HEIGHT, 0)
        
        if self.battle_state:
            if self.battle_state.winner == 0:
                text = "VICTORY!"
                color = 10
            else:
                text = "DEFEAT..."
                color = 8
            
            pyxel.text(100, 80, text, color)
        
        pyxel.text(70, 110, "Z/R: Restart  X: Title", 7)


def run_app() -> None:
    """Launch the Pyxel application."""
    MedaBattleApp()
