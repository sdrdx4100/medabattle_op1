/**
 * @file bindings.cpp
 * @brief pybind11 bindings for the battle engine.
 */

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "battle_core.hpp"

namespace py = pybind11;
using namespace medabattle;

/**
 * @brief Convert Python dict to ActionInput.
 */
ActionInput dict_to_action_input(const py::dict& d) {
    ActionInput input;
    
    if (d.contains("actor_name")) {
        input.actor_name = d["actor_name"].cast<std::string>();
    }
    if (d.contains("actor_team")) {
        input.actor_team = d["actor_team"].cast<int>();
    }
    if (d.contains("part_name")) {
        input.part_name = d["part_name"].cast<std::string>();
    }
    if (d.contains("action_type")) {
        input.action_type = d["action_type"].cast<std::string>();
    }
    if (d.contains("success_value")) {
        input.success_value = d["success_value"].cast<int>();
    }
    if (d.contains("power")) {
        input.power = d["power"].cast<int>();
    }
    if (d.contains("hit_bonus")) {
        input.hit_bonus = d["hit_bonus"].cast<int>();
    }
    if (d.contains("target_name")) {
        input.target_name = d["target_name"].cast<std::string>();
    }
    if (d.contains("target_team")) {
        input.target_team = d["target_team"].cast<int>();
    }
    if (d.contains("target_evade")) {
        input.target_evade = d["target_evade"].cast<int>();
    }
    if (d.contains("target_part") && !d["target_part"].is_none()) {
        input.target_part = d["target_part"].cast<std::string>();
    }
    
    return input;
}

/**
 * @brief Convert ActionResult to Python dict.
 */
py::dict action_result_to_dict(const ActionResult& result) {
    py::dict d;
    d["hit"] = result.hit;
    d["damage"] = result.damage;
    d["is_critical"] = result.is_critical;
    d["effect"] = result.effect;
    return d;
}

/**
 * @brief Simulate a single action.
 * @param action_dict Python dict with action parameters
 * @return Python dict with action result
 */
py::dict simulate_action(const py::dict& action_dict) {
    ActionInput input = dict_to_action_input(action_dict);
    ActionResult result = BattleCore::simulate_action(input);
    return action_result_to_dict(result);
}

/**
 * @brief Update ATB gauges for all robots.
 * @param state_dict Python dict with battle state
 * @param delta Time delta
 * @return Python dict with updated robot states
 */
py::dict update_atb(const py::dict& state_dict, double delta) {
    std::vector<RobotATBState> robots;
    
    // Extract robots from both teams
    auto process_team = [&robots](const py::list& team) {
        for (const auto& robot : team) {
            py::dict r = robot.cast<py::dict>();
            RobotATBState state;
            state.name = r["name"].cast<std::string>();
            state.current_gauge = r.contains("atb_gauge") ? r["atb_gauge"].cast<double>() : 0.0;
            
            // Get charge stat from legs
            if (r.contains("legs")) {
                py::dict legs = r["legs"].cast<py::dict>();
                state.charge_stat = legs.contains("charge") ? legs["charge"].cast<int>() : 20;
            }
            
            // Check if functional (head not destroyed)
            if (r.contains("head")) {
                py::dict head = r["head"].cast<py::dict>();
                int armor = head.contains("armor") ? head["armor"].cast<int>() : 0;
                state.is_functional = armor > 0;
            }
            
            robots.push_back(state);
        }
    };
    
    if (state_dict.contains("team_a")) {
        process_team(state_dict["team_a"].cast<py::list>());
    }
    if (state_dict.contains("team_b")) {
        process_team(state_dict["team_b"].cast<py::list>());
    }
    
    // Calculate new gauges
    std::vector<double> new_gauges = BattleCore::update_atb_batch(robots, delta);
    
    // Build result
    py::dict result;
    py::list robot_updates;
    
    for (size_t i = 0; i < robots.size(); ++i) {
        py::dict update;
        update["name"] = robots[i].name;
        update["atb_gauge"] = new_gauges[i];
        robot_updates.append(update);
    }
    
    result["robots"] = robot_updates;
    return result;
}

PYBIND11_MODULE(battle_engine, m) {
    m.doc() = "High-performance battle engine for Medabot simulation";
    
    m.def("simulate_action", &simulate_action,
          py::arg("action_dict"),
          "Simulate a single combat action");
    
    m.def("update_atb", &update_atb,
          py::arg("state_dict"),
          py::arg("delta"),
          "Update ATB gauges for all robots");
    
    // Expose RuleConfig for advanced usage
    py::class_<RuleConfig>(m, "RuleConfig")
        .def(py::init<>())
        .def_readwrite("base_hit_chance", &RuleConfig::base_hit_chance)
        .def_readwrite("max_hit_chance", &RuleConfig::max_hit_chance)
        .def_readwrite("min_hit_chance", &RuleConfig::min_hit_chance)
        .def_readwrite("damage_variance_min", &RuleConfig::damage_variance_min)
        .def_readwrite("damage_variance_max", &RuleConfig::damage_variance_max)
        .def_readwrite("critical_multiplier", &RuleConfig::critical_multiplier)
        .def_readwrite("critical_chance", &RuleConfig::critical_chance)
        .def_readwrite("atb_max", &RuleConfig::atb_max)
        .def_readwrite("atb_base_speed", &RuleConfig::atb_base_speed)
        .def_readwrite("min_damage", &RuleConfig::min_damage)
        .def_static("default_config", &RuleConfig::default_config);
}
