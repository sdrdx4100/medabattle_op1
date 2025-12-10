/**
 * @file battle_core.cpp
 * @brief High-performance battle calculations for Medabot simulation.
 * 
 * This module provides optimized implementations for:
 * - Hit/miss calculations
 * - Damage calculations
 * - ATB gauge updates
 */

#include "battle_core.hpp"
#include <algorithm>
#include <cmath>
#include <random>

namespace medabattle {

// Thread-local random engine for thread safety
static thread_local std::mt19937 rng(std::random_device{}());

RuleConfig RuleConfig::default_config() {
    return RuleConfig{
        .base_hit_chance = 50.0,
        .max_hit_chance = 95.0,
        .min_hit_chance = 5.0,
        .damage_variance_min = 0.8,
        .damage_variance_max = 1.2,
        .critical_multiplier = 1.5,
        .critical_chance = 10.0,
        .atb_max = 100.0,
        .atb_base_speed = 1.0,
        .min_damage = 1,
    };
}

double BattleCore::calculate_hit_chance(
    int attacker_success,
    int defender_evade,
    const std::vector<int>& modifiers,
    const RuleConfig& config
) {
    int total_mod = 0;
    for (int mod : modifiers) {
        total_mod += mod;
    }
    
    double hit_chance = config.base_hit_chance 
        + static_cast<double>(attacker_success)
        - static_cast<double>(defender_evade)
        + static_cast<double>(total_mod);
    
    return std::clamp(hit_chance, config.min_hit_chance, config.max_hit_chance);
}

int BattleCore::calculate_damage(
    int power,
    double variance,
    int defense,
    bool is_critical,
    const RuleConfig& config
) {
    double crit_mult = is_critical ? config.critical_multiplier : 1.0;
    double damage = static_cast<double>(power) * variance * crit_mult 
        - static_cast<double>(defense);
    
    return std::max(config.min_damage, static_cast<int>(damage));
}

double BattleCore::calculate_atb_increment(
    int charge_stat,
    double base_delta,
    const RuleConfig& config
) {
    if (charge_stat <= 0) {
        charge_stat = 1;
    }
    
    double speed = config.atb_base_speed * 100.0 / static_cast<double>(charge_stat);
    return base_delta * speed;
}

bool BattleCore::roll_hit(double hit_chance) {
    std::uniform_real_distribution<double> dist(0.0, 100.0);
    return dist(rng) < hit_chance;
}

bool BattleCore::roll_critical(const RuleConfig& config) {
    std::uniform_real_distribution<double> dist(0.0, 100.0);
    return dist(rng) < config.critical_chance;
}

double BattleCore::roll_variance(const RuleConfig& config) {
    std::uniform_real_distribution<double> dist(
        config.damage_variance_min,
        config.damage_variance_max
    );
    return dist(rng);
}

ActionResult BattleCore::simulate_action(const ActionInput& input, const RuleConfig& config) {
    ActionResult result;
    result.hit = false;
    result.damage = 0;
    result.is_critical = false;
    result.effect = "";
    
    // Calculate hit chance
    double hit_chance = calculate_hit_chance(
        input.success_value + input.hit_bonus,
        input.target_evade,
        {},
        config
    );
    
    // Roll for hit
    result.hit = roll_hit(hit_chance);
    
    if (!result.hit) {
        result.effect = "Miss!";
        return result;
    }
    
    // Process based on action type
    if (input.action_type == "SHOOT" || input.action_type == "STRIKE") {
        result.is_critical = roll_critical(config);
        double variance = roll_variance(config);
        result.damage = calculate_damage(input.power, variance, 0, result.is_critical, config);
        result.effect = result.is_critical ? "Critical Hit!" : "Hit!";
    } else if (input.action_type == "SUPPORT") {
        // Healing is negative damage
        result.damage = -static_cast<int>(input.power * 0.5);
        result.effect = "Healed!";
    } else if (input.action_type == "DISRUPT") {
        result.effect = "Disrupted!";
    } else if (input.action_type == "DEFEND") {
        result.effect = "Defended!";
    }
    
    return result;
}

std::vector<double> BattleCore::update_atb_batch(
    const std::vector<RobotATBState>& robots,
    double delta,
    const RuleConfig& config
) {
    std::vector<double> new_gauges;
    new_gauges.reserve(robots.size());
    
    for (const auto& robot : robots) {
        if (!robot.is_functional) {
            new_gauges.push_back(0.0);
            continue;
        }
        
        double increment = calculate_atb_increment(robot.charge_stat, delta, config);
        double new_gauge = std::min(robot.current_gauge + increment, config.atb_max * 2.0);
        new_gauges.push_back(new_gauge);
    }
    
    return new_gauges;
}

} // namespace medabattle
