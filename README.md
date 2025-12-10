# MedaBattle OP1

A Medabot-style robot battle simulation game with Python + Pyxel UI and C++ high-performance battle engine.

## Features

- **Modular Robot Construction**: Assemble robots with Head, Right Arm, Left Arm, and Leg parts
- **Medal/Personality System**: AI behavior influenced by personality traits
- **Turn-based Battle**: Simple turn-based combat (ATB extensible)
- **Symbol-based UI**: All units displayed as □ symbols with color coding
- **High-performance Engine**: C++ battle core with pybind11 bindings
- **Balance Analysis**: Polars/DuckDB powered simulation analysis

## Directory Structure

```
project root/
├── pyproject.toml          # Python project configuration
├── README.md               # This file
├── src/
│   ├── core/
│   │   ├── models.py       # Robot, Part, Medal data models
│   │   ├── battle_logic.py # Battle state, turn management, AI strategies
│   │   ├── rules.py        # Combat rules (hit, damage, ATB)
│   │   └── simulator.py    # Batch simulation utilities
│   ├── engine/
│   │   ├── CMakeLists.txt  # C++ build configuration
│   │   ├── battle_core.cpp # C++ battle processing
│   │   ├── bindings.cpp    # pybind11 Python bindings
│   │   └── __init__.py     # Engine module init
│   ├── ui/
│   │   ├── pyxel_app.py    # Pyxel-based playable UI
│   │   └── renderer.py     # Symbol-based rendering
│   ├── data/
│   │   ├── parts.yaml      # Part definitions
│   │   ├── medals.yaml     # Medal/personality definitions
│   │   └── actions.yaml    # Action definitions
│   └── analysis/
│       └── balance_analysis.py  # Polars/DuckDB analysis
├── tests/
│   ├── test_models.py
│   ├── test_battle_logic.py
│   └── test_engine_integration.py
├── configs/
│   └── sample.yaml         # Sample battle configuration
└── data/
    └── logs/               # Simulation logs output
```

## Installation

```bash
# Install Python dependencies
pip install -e .

# For development
pip install -e ".[dev]"

# For analysis features
pip install -e ".[analysis]"
```

### Building C++ Engine (Optional)

```bash
cd src/engine
mkdir build && cd build
cmake ..
make
```

## Usage

### Play Mode (Pyxel UI)

```bash
python -m src.main play
```

### Simulation Mode

```bash
python -m src.main simulate --config configs/sample.yaml --n 1000
```

### Controls (Play Mode)

- **Arrow Keys**: Move cursor / Select targets
- **Z**: Confirm selection
- **X**: Cancel / Back
- **Space**: Advance turn
- **R**: Reset battle
- **Q**: Quit

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

- Python: Type hints, clean architecture
- C++: Modern C++17 style

## License

MIT License - see LICENSE file