# tools/hsi/constants.py
"""Every vanilla 1.14.5 number the generator uses. Source: common/defines/00_defines.txt (D) and
common/script_values/00_diplomacy_values.txt (DV) unless noted. Re-read these on any game patch."""
STATE_BASELINE = 5.0                 # D:1121 WAR_GOAL_INFAMY_STATE_BASELINE
WORLD_SHARE_SCALE = 10000.0          # D:1113 WAR_GOAL_INFAMY_WORLD_SHARE_SCALE
POP_WEIGHT = 0.375                   # D:1114 WAR_GOAL_INFAMY_POPULATION_WEIGHT
GDP_WEIGHT = 0.375                   # D:1115 WAR_GOAL_INFAMY_GDP_WEIGHT
SHARE_MAX = 15.0                     # D:1117 / D:1118 (population, GDP)
SHARE_SOFT_CAP = 10.0                # D:1119 WAR_GOAL_INFAMY_SHARE_SOFT_CAP
SHARE_SOFT_CAP_SLOPE = 0.5           # D:1120 WAR_GOAL_INFAMY_SHARE_SOFT_CAP_SLOPE
STANDING = {                         # D:1149-1152
    "capital": 2.0, "homeland": 1.5, "incorporated": 1.0, "unincorporated": 0.5,
}
HOMELAND_FACTOR = -0.25              # D:1161 WAR_GOAL_INFAMY_HOMELAND_FACTOR
HOMELAND_BONUS_FACTOR = -0.1         # D:1162
SHARED_LANGUAGE_FACTOR = -0.15       # D:1153
SHARED_LANGUAGE_BONUS_FACTOR = -0.1  # D:1154
CLAIM_FACTOR = -0.75                 # D:1155
ADJACENCY_FACTOR = -0.1              # D:1156
SCRIPTED_UNIFICATION_FACTOR = -0.7   # D:1157
INTEREST_INCREASE_HIGH = 0.25        # DV:1068 (tier < 2)
INTEREST_INCREASE_MEDIUM = 0.10      # DV:1069 (tier < 3)
INTEREST_DECREASE_MEDIUM = -0.20     # DV:1070 (tier >= 5)
INTEREST_INCREASE_MAX_TIER = 2       # DV:1072
INTEREST_DECREASE_MIN_TIER = 5       # DV:1073
STATE_MIN = 1.0                      # D:1148 WAR_GOAL_INFAMY_MINIMUM (per state)
GOAL_MIN = 1.0                       # D:1148 (per war goal, after all multipliers)
SUBJECT_MULT = 0.25                  # D:1164 rebellious, D:1165 loyal (LD < 25, D:1167)
RULE_MULT = {                        # D:1122-1125; standard has no flag (00_game_rules.txt:97-117)
    "very_low": 0.5, "low": 0.75, "standard": 1.0, "high": 1.25, "very_high": 1.5,
}
RULE_FLAGS = {                       # 00_game_rules.txt:100-117
    "very_low": "infamy_generation_very_low", "low": "infamy_generation_low",
    "high": "infamy_generation_high", "very_high": "infamy_generation_very_high",
}
REFUND = {                           # fraction of the accrued charge returned when the goal is dropped
    "dropped_backdown": 0.75,        # D:1172 WAR_GOAL_INFAMY_DIPLO_PLAY_BACK_DOWN_REFUND
    "dropped_backer": 1.0,           # D:1173 WAR_GOAL_INFAMY_DIPLO_PLAY_BACKER_REFUND
    "dropped_peace": 0.5,            # D:1174 WAR_GOAL_INFAMY_PEACE_REFUND
}
VICTIM_REDUCTION = 0.5               # D:1175 WAR_GOAL_INFAMY_REDUCTION_FOR_TARGET (spec H2)
DECAY_PER_YEAR = 5.0                 # D:1006 BASE_YEARLY_INFAMY_DECAY_RATE
DAYS_PER_YEAR = 365.25               # declared model choice (spec §10)
INFAMY_MIN = 0.0                     # D:1000
INFAMY_MAX = 1000.0                  # D:1001
RANK_SCALING = {                     # common/country_ranks/00_country_ranks.txt: (infamy_aggressor_scaling, infamy_target_scaling)
    "great_power": (0.20, 0.20),                    # :29-30
    "major_power": (0.10, 0.10),                    # :67-68
    "minor_power": (0.0, 0.0),                      # :92-119 carry no scaling lines
    "insignificant_power": (-0.10, -0.10),          # :125-126
    "unrecognized_major_power": (0.50, -0.30),      # :161-162
    "unrecognized_regional_power": (0.40, -0.40),   # :196-197
    "unrecognized_power": (0.30, -0.50),            # :228-229
    "decentralized_power": (0.0, 0.0),              # :254-… carries no scaling lines
}
RANK_CODES = {7: "great_power", 6: "major_power", 5: "minor_power", 4: "insignificant_power",   # probe_gen.RANK_CODES
              3: "unrecognized_major_power", 2: "unrecognized_regional_power", 1: "unrecognized_power", 0: "decentralized_power"}
FALLBACK_RANK = {"recognized": "minor_power", "unrecognized": "unrecognized_power",   # declared for actors without a 1836 tag (ruling 2026-10-14)
                 "decentralized": "decentralized_power"}
WINDOW_START = "1816-01-01"          # spec §5
WINDOW_END = "1835-12-31"            # spec §5
HORIZON = "1836-01-01"               # spec §7, balance read at the beginning of this day
