/**
 * @file battle_core.hpp
 * @brief Header file for battle core calculations.
 */

#ifndef BATTLE_CORE_HPP
#define BATTLE_CORE_HPP

#include <string>
#include <vector>

namespace medabattle {

/**
 * @brief Configuration for battle rules.
 */
struct RuleConfig {
    double base_hit_chance = 50.0;
    double max_hit_chance = 95.0;
    double min_hit_chance = 5.0;
    double damage_variance_min = 0.8;
    double damage_variance_max = 1.2;
    double critical_multiplier = 1.5;
    double critical_chance = 10.0;
    double atb_max = 100.0;
    double atb_base_speed = 1.0;
    int min_damage = 1;
    
    static RuleConfig default_config();
};

/**
 * @brief Input for action simulation.
 */
struct ActionInput {
    std::string actor_name;
    int actor_team = 0;
    std::string part_name;
    std::string action_type;
    int success_value = 50;
    int power = 30;
    int hit_bonus = 0;
    std::string target_name;
    int target_team = 1;
    int target_evade = 0;
    std::string target_part;
};

/**
 * @brief Result of action simulation.
 */
struct ActionResult {
    bool hit = false;
    int damage = 0;
    bool is_critical = false;
    std::string effect;
};

/**
 * @brief Robot state for ATB calculations.
 */
struct RobotATBState {
    std::string name;
    double current_gauge = 0.0;
    int charge_stat = 20;
    bool is_functional = true;
};

/**
 * @brief Core battle calculation functions.
 */
class BattleCore {
public:
    /**
     * @brief Calculate hit chance for an attack.
     * @param attacker_success Attacker's success value
     * @param defender_evade Defender's evasion value
     * @param modifiers Additional modifiers
     * @param config Rule configuration
     * @return Hit chance as percentage (0-100)
     */
    static double calculate_hit_chance(
        int attacker_success,
        int defender_evade,
        const std::vector<int>& modifiers = {},
        const RuleConfig& config = RuleConfig::default_config()
    );
    
    /**
     * @brief Calculate damage for an attack.
     * @param power Base attack power
     * @param variance Random variance multiplier
     * @param defense Defender's defense value
     * @param is_critical Whether this is a critical hit
     * @param config Rule configuration
     * @return Final damage value
     */
    static int calculate_damage(
        int power,
        double variance = 1.0,
        int defense = 0,
        bool is_critical = false,
        const RuleConfig& config = RuleConfig::default_config()
    );
    
    /**
     * @brief Calculate ATB gauge increment.
     * @param charge_stat Robot's charge/speed stat
     * @param base_delta Base time units passed
     * @param config Rule configuration
     * @return ATB increment amount
     */
    static double calculate_atb_increment(
        int charge_stat,
        double base_delta,
        const RuleConfig& config = RuleConfig::default_config()
    );
    
    /**
     * @brief Roll for hit success.
     * @param hit_chance Hit chance percentage
     * @return True if hit succeeds
     */
    static bool roll_hit(double hit_chance);
    
    /**
     * @brief Roll for critical hit.
     * @param config Rule configuration
     * @return True if critical hit
     */
    static bool roll_critical(const RuleConfig& config = RuleConfig::default_config());
    
    /**
     * @brief Roll damage variance.
     * @param config Rule configuration
     * @return Variance multiplier
     */
    static double roll_variance(const RuleConfig& config = RuleConfig::default_config());
    
    /**
     * @brief Simulate a single action.
     * @param input Action input parameters
     * @param config Rule configuration
     * @return Action result
     */
    static ActionResult simulate_action(
        const ActionInput& input,
        const RuleConfig& config = RuleConfig::default_config()
    );
    
    /**
     * @brief Update ATB gauges for multiple robots.
     * @param robots Robot ATB states
     * @param delta Time delta
     * @param config Rule configuration
     * @return New ATB gauge values
     */
    static std::vector<double> update_atb_batch(
        const std::vector<RobotATBState>& robots,
        double delta,
        const RuleConfig& config = RuleConfig::default_config()
    );
};

} // namespace medabattle

#endif // BATTLE_CORE_HPP
