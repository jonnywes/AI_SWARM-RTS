# constants.py

# ==========================================
# UI & DISPLAY SETTINGS
# ==========================================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 30

MAP_WIDTH = 800
MAP_HEIGHT = 720
TERMINAL_WIDTH = SCREEN_WIDTH - MAP_WIDTH
TERMINAL_HEIGHT = 720
INPUT_BOX_HEIGHT = 200

COLOR_BG_MAP = (30, 30, 30)
COLOR_BG_TERMINAL = (15, 15, 15)
COLOR_TEXT = (200, 200, 200)
COLOR_INPUT_BG = (40, 40, 40)
COLOR_HIGHLIGHT = (100, 200, 100)
COLOR_HIVE_BLUE = (50, 150, 200)  
COLOR_HIVE_RED = (200, 50, 50)    

# ==========================================
# GAMEPLAY MECHANICS
# ==========================================
STARTING_FOOD = 100
STARTING_WORKERS = 5
STARTING_WARRIORS = 0

UPKEEP_QUEEN = 5
UPKEEP_WARRIOR = 1
UPKEEP_WORKER = 0 

GATHER_RATE_BASE = 2
GATHER_RATE_BOOSTED = 4 

COST_WORKER = 10
COST_WARRIOR = 15
COST_QUEEN = 50 

FACTION_PLAYER = "BLUE"
FACTION_ENEMY = "RED"
MAX_HIVES = 20 # Hard cap for performance

# ==========================================
# AI / PARSER CONSTANTS
# ==========================================
TARGET_QUEEN = "QUEEN"

# Macro Objectives (LLM Uses These)
OBJ_BALANCED = "Balanced"
OBJ_AGGRESSIVE = "Aggressive"
OBJ_ECONOMY = "Economy"

ACTION_SET_OBJ_BALANCED = f"Set Objective: {OBJ_BALANCED}"
ACTION_SET_OBJ_AGGRESSIVE = f"Set Objective: {OBJ_AGGRESSIVE}"
ACTION_SET_OBJ_ECONOMY = f"Set Objective: {OBJ_ECONOMY}"

VALID_ACTIONS = [
    ACTION_SET_OBJ_BALANCED,
    ACTION_SET_OBJ_AGGRESSIVE,
    ACTION_SET_OBJ_ECONOMY
]

# Internal Micro Actions (The Queen AI Uses These)
ACTION_GATHER_FOOD = "Focus on gathering food"
ACTION_PRODUCE_WORKERS = "Produce Workers"
ACTION_PRODUCE_WARRIORS = "Produce Warriors"
ACTION_PRODUCE_QUEEN = "Produce a new queen"
ACTION_ATTACK = "Launch Attack"