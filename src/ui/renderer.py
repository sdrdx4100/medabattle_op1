"""
Symbol-based rendering for battle visualization.

This module handles drawing robots and battle elements
using simple symbols (□, ■, etc.) and colors.
"""

from __future__ import annotations

import pyxel

from ..core.models import Part, PartType, Robot


class BattleRenderer:
    """
    Renderer for battle visualization using symbols.
    
    All units are represented using simple shapes and colors:
    - Body: White square
    - Head: Blue square
    - Right Arm: Red square
    - Left Arm: Green square
    - Legs: Yellow square
    """
    
    # Colors
    COLOR_BODY = 7       # White
    COLOR_HEAD = 12      # Blue
    COLOR_RIGHT_ARM = 8  # Red
    COLOR_LEFT_ARM = 11  # Green
    COLOR_LEGS = 10      # Yellow
    COLOR_DESTROYED = 5  # Dark gray
    COLOR_HIGHLIGHT = 9  # Orange
    
    # Grid settings
    GRID_OFFSET_X = 32
    GRID_OFFSET_Y = 24
    CELL_SIZE = 16
    GRID_WIDTH = 10
    GRID_HEIGHT = 7
    
    # Part symbol size
    PART_SIZE = 6
    
    def draw_battlefield(self) -> None:
        """Draw the battle grid."""
        for x in range(self.GRID_WIDTH):
            for y in range(self.GRID_HEIGHT):
                px = self.GRID_OFFSET_X + x * self.CELL_SIZE
                py = self.GRID_OFFSET_Y + y * self.CELL_SIZE
                
                # Draw cell border
                pyxel.rectb(px, py, self.CELL_SIZE, self.CELL_SIZE, 1)
    
    def grid_to_pixel(self, gx: int, gy: int) -> tuple[int, int]:
        """
        Convert grid coordinates to pixel coordinates.
        
        Args:
            gx: Grid X position
            gy: Grid Y position
            
        Returns:
            Tuple of (pixel_x, pixel_y)
        """
        px = self.GRID_OFFSET_X + gx * self.CELL_SIZE + self.CELL_SIZE // 2
        py = self.GRID_OFFSET_Y + gy * self.CELL_SIZE + self.CELL_SIZE // 2
        return (px, py)
    
    def draw_robot(
        self,
        robot: Robot,
        is_highlighted: bool = False,
    ) -> None:
        """
        Draw a robot on the battlefield.
        
        Args:
            robot: Robot to draw
            is_highlighted: Whether to highlight (current actor)
        """
        gx, gy = robot.position
        cx, cy = self.grid_to_pixel(gx, gy)
        
        # Draw highlight if current actor
        if is_highlighted:
            pyxel.circb(cx, cy, 10, self.COLOR_HIGHLIGHT)
        
        # Draw body (center)
        body_color = self.COLOR_BODY if robot.is_functional else self.COLOR_DESTROYED
        self._draw_part_symbol(cx - 3, cy - 3, body_color)
        
        # Draw head (top)
        head_color = self._get_part_color(robot.head, self.COLOR_HEAD)
        self._draw_part_symbol(cx - 3, cy - 9, head_color)
        
        # Draw right arm (right side)
        rarm_color = self._get_part_color(robot.right_arm, self.COLOR_RIGHT_ARM)
        self._draw_part_symbol(cx + 3, cy - 3, rarm_color)
        
        # Draw left arm (left side)
        larm_color = self._get_part_color(robot.left_arm, self.COLOR_LEFT_ARM)
        self._draw_part_symbol(cx - 9, cy - 3, larm_color)
        
        # Draw legs (bottom)
        legs_color = self._get_part_color(robot.legs, self.COLOR_LEGS)
        self._draw_part_symbol(cx - 3, cy + 3, legs_color)
        
        # Draw team indicator
        team_color = 12 if robot.team == 0 else 8
        pyxel.pset(cx, cy - 11, team_color)
    
    def _draw_part_symbol(self, x: int, y: int, color: int) -> None:
        """
        Draw a part as a filled square.
        
        Args:
            x: Top-left X position
            y: Top-left Y position
            color: Fill color
        """
        pyxel.rect(x, y, self.PART_SIZE, self.PART_SIZE, color)
    
    def _get_part_color(self, part: Part, base_color: int) -> int:
        """
        Get color for a part based on its state.
        
        Args:
            part: Part to check
            base_color: Color when healthy
            
        Returns:
            Appropriate color
        """
        if part.is_destroyed:
            return self.COLOR_DESTROYED
        return base_color
    
    def draw_part_info(
        self,
        x: int,
        y: int,
        part: Part,
    ) -> int:
        """
        Draw detailed part information.
        
        Args:
            x: Start X position
            y: Start Y position
            part: Part to display
            
        Returns:
            Y position after drawing
        """
        # Part name and type
        color = 7 if not part.is_destroyed else 5
        pyxel.text(x, y, f"{part.name}", color)
        y += 8
        
        # Stats
        pyxel.text(x, y, f"  HP:{part.armor} PWR:{part.power}", color)
        y += 8
        
        return y
    
    def draw_robot_detail(
        self,
        x: int,
        y: int,
        robot: Robot,
    ) -> None:
        """
        Draw detailed robot information panel.
        
        Args:
            x: Start X position
            y: Start Y position
            robot: Robot to display
        """
        # Robot name
        color = 7 if robot.is_functional else 8
        pyxel.text(x, y, robot.name, color)
        y += 12
        
        # Medal/personality
        pyxel.text(x, y, f"Medal: {robot.medal.name}", 6)
        y += 10
        
        # Parts
        for part in robot.parts:
            y = self.draw_part_info(x, y, part)
    
    def draw_atb_gauge(
        self,
        x: int,
        y: int,
        robot: Robot,
        width: int = 50,
    ) -> None:
        """
        Draw ATB gauge for a robot.
        
        Args:
            x: Start X position
            y: Start Y position
            robot: Robot whose gauge to draw
            width: Gauge width in pixels
        """
        # Background
        pyxel.rect(x, y, width, 4, 1)
        
        # Fill based on ATB
        fill_width = int((robot.atb_gauge / 100.0) * width)
        fill_width = min(fill_width, width)
        
        if fill_width > 0:
            color = 10 if robot.atb_gauge >= 100 else 6
            pyxel.rect(x, y, fill_width, 4, color)
        
        # Border
        pyxel.rectb(x, y, width, 4, 7)
    
    def draw_action_effect(
        self,
        x: int,
        y: int,
        effect_type: str,
        frame: int,
    ) -> None:
        """
        Draw an action effect animation.
        
        Args:
            x: Center X position
            y: Center Y position
            effect_type: Type of effect (hit, miss, heal)
            frame: Animation frame
        """
        if effect_type == "hit":
            # Expanding circle
            radius = 3 + (frame % 5)
            pyxel.circb(x, y, radius, 8)
        elif effect_type == "miss":
            # X mark
            size = 4
            pyxel.line(x - size, y - size, x + size, y + size, 6)
            pyxel.line(x + size, y - size, x - size, y + size, 6)
        elif effect_type == "heal":
            # Plus sign
            size = 3
            pyxel.line(x - size, y, x + size, y, 11)
            pyxel.line(x, y - size, x, y + size, 11)
