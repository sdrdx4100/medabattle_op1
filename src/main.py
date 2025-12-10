"""
Main entry point for MedaBattle.

Usage:
    python -m src.main play           - Start Pyxel UI for interactive play
    python -m src.main simulate       - Run batch simulation
    python -m src.main analyze <file> - Analyze simulation results
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cmd_play(args: argparse.Namespace) -> int:
    """Start the Pyxel UI for interactive play."""
    try:
        from .ui.pyxel_app import run_app
        run_app()
        return 0
    except ImportError as e:
        print(f"Error: Could not import Pyxel UI: {e}")
        print("Make sure pyxel is installed: pip install pyxel")
        return 1


def cmd_simulate(args: argparse.Namespace) -> int:
    """Run batch battle simulation."""
    from .core.simulator import Simulator, SimulationConfig
    
    # Load or create config
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}")
            return 1
        config = SimulationConfig.from_yaml(config_path)
    else:
        config = SimulationConfig()
    
    # Override with command line args
    if args.strategy_a:
        config.team_a_strategy = args.strategy_a
    if args.strategy_b:
        config.team_b_strategy = args.strategy_b
    if args.seed is not None:
        config.seed = args.seed
    
    print(f"Running {args.n} battles...")
    print(f"Team A strategy: {config.team_a_strategy}")
    print(f"Team B strategy: {config.team_b_strategy}")
    
    simulator = Simulator(config)
    simulator.run_simulation(args.n)
    
    # Print summary
    summary = simulator.get_summary()
    print("\n=== Simulation Results ===")
    print(f"Total Battles: {summary['total_battles']}")
    print(f"Team A Wins: {summary['team_a_wins']} ({summary['team_a_win_rate']:.1f}%)")
    print(f"Team B Wins: {summary['team_b_wins']} ({summary['team_b_win_rate']:.1f}%)")
    print(f"Draws: {summary['draws']}")
    print(f"Average Turns: {summary['average_turns']:.1f}")
    
    # Export results
    if args.output:
        output_path = Path(args.output)
        if output_path.suffix == ".csv":
            simulator.export_to_csv(output_path)
        else:
            simulator.export_to_json(output_path)
        print(f"\nResults saved to: {output_path}")
    
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze simulation results."""
    try:
        from .analysis.balance_analysis import analyze_simulation_file
        
        results_path = Path(args.file)
        if not results_path.exists():
            print(f"Error: Results file not found: {results_path}")
            return 1
        
        analyze_simulation_file(results_path)
        return 0
    except ImportError as e:
        print(f"Error: Could not import analysis module: {e}")
        print("Make sure polars is installed: pip install polars")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="medabattle",
        description="Medabot-style robot battle simulation",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Play command
    play_parser = subparsers.add_parser(
        "play",
        help="Start interactive Pyxel UI",
    )
    play_parser.set_defaults(func=cmd_play)
    
    # Simulate command
    sim_parser = subparsers.add_parser(
        "simulate",
        help="Run batch battle simulation",
    )
    sim_parser.add_argument(
        "-n",
        type=int,
        default=100,
        help="Number of battles to simulate (default: 100)",
    )
    sim_parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration YAML file",
    )
    sim_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output file path (CSV or JSON)",
    )
    sim_parser.add_argument(
        "--strategy-a",
        type=str,
        choices=["random", "aggressive", "defensive", "medal"],
        help="Strategy for team A",
    )
    sim_parser.add_argument(
        "--strategy-b",
        type=str,
        choices=["random", "aggressive", "defensive", "medal"],
        help="Strategy for team B",
    )
    sim_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    sim_parser.set_defaults(func=cmd_simulate)
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze simulation results",
    )
    analyze_parser.add_argument(
        "file",
        type=str,
        help="Path to results file (CSV or Parquet)",
    )
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
