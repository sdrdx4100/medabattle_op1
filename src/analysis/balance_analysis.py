"""
Balance analysis tools for simulation results.

This module provides analysis capabilities using Polars
for processing simulation data and extracting insights.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

try:
    import polars as pl
    HAS_POLARS = True
except ImportError:
    pl = None
    HAS_POLARS = False


class BalanceAnalyzer:
    """
    Analyzer for battle simulation results.
    
    Uses Polars for efficient data processing and analysis
    of simulation logs.
    """
    
    def __init__(self, data_path: Path | str | None = None):
        """
        Initialize the analyzer.
        
        Args:
            data_path: Path to simulation results (CSV or Parquet)
        """
        if not HAS_POLARS:
            raise ImportError(
                "Polars is required for balance analysis. "
                "Install with: pip install polars"
            )
        
        self.data_path = Path(data_path) if data_path else None
        self.df: pl.DataFrame | None = None
    
    def load_csv(self, path: Path | str) -> pl.DataFrame:
        """
        Load simulation results from CSV.
        
        Args:
            path: Path to CSV file
            
        Returns:
            Loaded DataFrame
        """
        self.data_path = Path(path)
        self.df = pl.read_csv(path)
        return self.df
    
    def load_parquet(self, path: Path | str) -> pl.DataFrame:
        """
        Load simulation results from Parquet.
        
        Args:
            path: Path to Parquet file
            
        Returns:
            Loaded DataFrame
        """
        self.data_path = Path(path)
        self.df = pl.read_parquet(path)
        return self.df
    
    def get_win_rates(self) -> dict[str, float]:
        """
        Calculate win rates for each team.
        
        Returns:
            Dictionary with team win rates
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        total = len(self.df)
        team_a_wins = self.df.filter(pl.col("winner") == 0).height
        team_b_wins = self.df.filter(pl.col("winner") == 1).height
        draws = self.df.filter(pl.col("winner").is_null()).height
        
        return {
            "team_a_win_rate": team_a_wins / total * 100 if total > 0 else 0,
            "team_b_win_rate": team_b_wins / total * 100 if total > 0 else 0,
            "draw_rate": draws / total * 100 if total > 0 else 0,
        }
    
    def get_turn_statistics(self) -> dict[str, float]:
        """
        Calculate statistics about battle duration.
        
        Returns:
            Dictionary with turn statistics
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        turns = self.df.select("turns")
        
        return {
            "avg_turns": turns.mean().item(),
            "min_turns": turns.min().item(),
            "max_turns": turns.max().item(),
            "median_turns": turns.median().item(),
        }
    
    def get_damage_statistics(self) -> dict[str, float]:
        """
        Calculate damage statistics.
        
        Returns:
            Dictionary with damage statistics
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        return {
            "avg_damage_team_a": self.df.select("total_damage_a").mean().item(),
            "avg_damage_team_b": self.df.select("total_damage_b").mean().item(),
            "max_damage_team_a": self.df.select("total_damage_a").max().item(),
            "max_damage_team_b": self.df.select("total_damage_b").max().item(),
        }
    
    def get_remaining_units_statistics(self) -> dict[str, float]:
        """
        Calculate statistics about remaining units.
        
        Returns:
            Dictionary with remaining unit statistics
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        return {
            "avg_remaining_team_a": self.df.select("team_a_remaining").mean().item(),
            "avg_remaining_team_b": self.df.select("team_b_remaining").mean().item(),
        }
    
    def analyze_by_config(self) -> pl.DataFrame:
        """
        Analyze results grouped by configuration.
        
        Returns:
            DataFrame with per-config statistics
        """
        if self.df is None:
            raise ValueError("No data loaded")
        
        return self.df.group_by("config_name").agg([
            pl.count().alias("battles"),
            (pl.col("winner") == 0).sum().alias("team_a_wins"),
            (pl.col("winner") == 1).sum().alias("team_b_wins"),
            pl.col("turns").mean().alias("avg_turns"),
            pl.col("total_damage_a").mean().alias("avg_damage_a"),
            pl.col("total_damage_b").mean().alias("avg_damage_b"),
        ])
    
    def get_full_report(self) -> dict[str, Any]:
        """
        Generate a comprehensive analysis report.
        
        Returns:
            Dictionary containing all statistics
        """
        return {
            "win_rates": self.get_win_rates(),
            "turn_statistics": self.get_turn_statistics(),
            "damage_statistics": self.get_damage_statistics(),
            "remaining_units": self.get_remaining_units_statistics(),
        }
    
    def print_report(self) -> None:
        """Print a formatted analysis report to console."""
        report = self.get_full_report()
        
        print("=" * 50)
        print("BATTLE SIMULATION ANALYSIS REPORT")
        print("=" * 50)
        
        print("\n--- Win Rates ---")
        wr = report["win_rates"]
        print(f"Team A Win Rate: {wr['team_a_win_rate']:.1f}%")
        print(f"Team B Win Rate: {wr['team_b_win_rate']:.1f}%")
        print(f"Draw Rate: {wr['draw_rate']:.1f}%")
        
        print("\n--- Turn Statistics ---")
        ts = report["turn_statistics"]
        print(f"Average Turns: {ts['avg_turns']:.1f}")
        print(f"Min Turns: {ts['min_turns']}")
        print(f"Max Turns: {ts['max_turns']}")
        print(f"Median Turns: {ts['median_turns']:.1f}")
        
        print("\n--- Damage Statistics ---")
        ds = report["damage_statistics"]
        print(f"Team A Avg Damage: {ds['avg_damage_team_a']:.1f}")
        print(f"Team B Avg Damage: {ds['avg_damage_team_b']:.1f}")
        
        print("\n--- Remaining Units ---")
        ru = report["remaining_units"]
        print(f"Team A Avg Remaining: {ru['avg_remaining_team_a']:.2f}")
        print(f"Team B Avg Remaining: {ru['avg_remaining_team_b']:.2f}")
        
        print("=" * 50)


def analyze_simulation_file(path: Path | str) -> None:
    """
    Quick analysis of a simulation results file.
    
    Args:
        path: Path to results file (CSV or Parquet)
    """
    path = Path(path)
    analyzer = BalanceAnalyzer()
    
    if path.suffix == ".csv":
        analyzer.load_csv(path)
    elif path.suffix in (".parquet", ".pq"):
        analyzer.load_parquet(path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    analyzer.print_report()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        analyze_simulation_file(sys.argv[1])
    else:
        print("Usage: python -m src.analysis.balance_analysis <results_file>")
