cmake_minimum_required(VERSION 3.18)
project(battle_engine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find pybind11
find_package(pybind11 CONFIG REQUIRED)

# Create the Python module
pybind11_add_module(battle_engine
    battle_core.cpp
    bindings.cpp
)

# Set output directory
set_target_properties(battle_engine PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
)

# Install target
install(TARGETS battle_engine
    LIBRARY DESTINATION ${CMAKE_CURRENT_SOURCE_DIR}
)
