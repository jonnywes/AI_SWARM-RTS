# engine.py
import constants
import random
import math

class Queen:
    def __init__(self, hive, queen_id):
        self.hive = hive
        self.queen_id = queen_id
        self.objective = constants.OBJ_BALANCED # Default state
        self.action_queued = None

class Hive:
    def __init__(self, hive_id, x, y, faction):
        self.hive_id = hive_id
        self.x = x
        self.y = y
        self.faction = faction 
        self.food = constants.STARTING_FOOD
        self.workers = constants.STARTING_WORKERS
        self.warriors = constants.STARTING_WARRIORS
        self.queens = []
        self.gathering_modifier = 1.0
        self.diaries = [] 
        self.is_destroyed = False
        
        # --- NEW: Combat Multipliers ---
        # Base stats. Can be upgraded later via technology!
        self.attack_multiplier = 1 
        self.defense_multiplier = 2 # Defender's Advantage (+1)

class Map:
    def __init__(self):
        self.hives = []

class GameEngine:
    def __init__(self):
        self.map = Map()
        self.turn_number = 1
        self.active_queens_queue = [] 
        self._next_hive_id = 1
        self._next_queen_id = 1
        self._create_initial_hives()

    def _create_initial_hives(self):
        blue_hive = Hive(self._next_hive_id, constants.MAP_WIDTH // 4, constants.MAP_HEIGHT // 2, constants.FACTION_PLAYER)
        self._next_hive_id += 1
        blue_queen = Queen(blue_hive, self._next_queen_id)
        self._next_queen_id += 1
        blue_hive.queens.append(blue_queen)
        self.map.hives.append(blue_hive)

        red_hive = Hive(self._next_hive_id, (constants.MAP_WIDTH // 4) * 3, constants.MAP_HEIGHT // 2, constants.FACTION_ENEMY)
        self._next_hive_id += 1
        red_queen = Queen(red_hive, self._next_queen_id)
        self._next_queen_id += 1
        red_hive.queens.append(red_queen)
        self.map.hives.append(red_hive)

    def start_turn(self):
        self.active_queens_queue.clear()
        for hive in self.map.hives:
            total_upkeep = (len(hive.queens) * constants.UPKEEP_QUEEN) + \
                           (hive.warriors * constants.UPKEEP_WARRIOR) + \
                           (hive.workers * constants.UPKEEP_WORKER)
            hive.food -= total_upkeep
            if hive.food < 0: hive.food = 0
            hive.gathering_modifier = 1.0
            
            if hive.faction == constants.FACTION_PLAYER:
                for queen in hive.queens:
                    self.active_queens_queue.append(queen)

    def process_queen_command(self, queen, parsed_data):
        action_str = parsed_data['action']
        if constants.OBJ_AGGRESSIVE in action_str:
            queen.objective = constants.OBJ_AGGRESSIVE
        elif constants.OBJ_ECONOMY in action_str:
            queen.objective = constants.OBJ_ECONOMY
        else:
            queen.objective = constants.OBJ_BALANCED

        log_entry = f"Turn {self.turn_number} | Hive {queen.hive.hive_id} | Objective Updated: {queen.objective}\nRemarks: {parsed_data['remarks']}"
        queen.hive.diaries.append(log_entry)

    def _get_random_enemy_hive(self, attacking_faction):
        enemies = [h for h in self.map.hives if h.faction != attacking_faction and not h.is_destroyed]
        return random.choice(enemies) if enemies else None

    def _determine_queen_action(self, hive, queen):
        obj = queen.objective
        
        if obj == constants.OBJ_ECONOMY:
            if hive.food < constants.COST_WORKER:
                queen.action_queued = constants.ACTION_GATHER_FOOD
            elif hive.workers < 25:
                queen.action_queued = constants.ACTION_PRODUCE_WORKERS
            elif hive.food >= constants.COST_QUEEN and len(self.map.hives) < constants.MAX_HIVES:
                queen.action_queued = constants.ACTION_PRODUCE_QUEEN
            else:
                queen.action_queued = constants.ACTION_GATHER_FOOD
                
        elif obj == constants.OBJ_AGGRESSIVE:
            if hive.food < constants.COST_WARRIOR:
                queen.action_queued = constants.ACTION_GATHER_FOOD
            elif hive.workers < 5: 
                queen.action_queued = constants.ACTION_PRODUCE_WORKERS
            elif hive.warriors < 8 and hive.food >= constants.COST_WARRIOR:
                queen.action_queued = constants.ACTION_PRODUCE_WARRIORS
            elif hive.warriors >= 8: 
                queen.action_queued = constants.ACTION_ATTACK
            else:
                queen.action_queued = constants.ACTION_GATHER_FOOD
                
        else: 
            if hive.food < constants.COST_WORKER:
                queen.action_queued = constants.ACTION_GATHER_FOOD
            elif hive.workers < 10:
                queen.action_queued = constants.ACTION_PRODUCE_WORKERS
            elif hive.warriors < 15 and hive.food >= constants.COST_WARRIOR:
                queen.action_queued = constants.ACTION_PRODUCE_WARRIORS
            elif hive.warriors >= 15:
                queen.action_queued = constants.ACTION_ATTACK
            elif hive.food >= constants.COST_QUEEN and len(self.map.hives) < constants.MAX_HIVES:
                queen.action_queued = constants.ACTION_PRODUCE_QUEEN
            else:
                queen.action_queued = constants.ACTION_GATHER_FOOD

    def _get_valid_spawn_location(self, origin_hive):
        for _ in range(20): 
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(150, 250) 
            new_x = origin_hive.x + distance * math.cos(angle)
            new_y = origin_hive.y + distance * math.sin(angle)
            
            new_x = max(40, min(constants.MAP_WIDTH - 80, new_x))
            new_y = max(40, min(constants.MAP_HEIGHT - 80, new_y))
            
            valid = True
            for other_hive in self.map.hives:
                if math.hypot(new_x - other_hive.x, new_y - other_hive.y) < 120: 
                    valid = False
                    break
            if valid:
                return new_x, new_y
        return None 

    def end_turn(self):
        for hive in self.map.hives:
            if not hive.is_destroyed:
                for queen in hive.queens:
                    self._determine_queen_action(hive, queen)

        for hive in self.map.hives:
            if hive.is_destroyed: continue
            
            for queen in hive.queens:
                action = queen.action_queued
                if action == constants.ACTION_GATHER_FOOD:
                    hive.gathering_modifier = constants.GATHER_RATE_BOOSTED / constants.GATHER_RATE_BASE
                elif action == constants.ACTION_PRODUCE_WORKERS and hive.food >= constants.COST_WORKER:
                    hive.food -= constants.COST_WORKER
                    hive.workers += 1
                elif action == constants.ACTION_PRODUCE_WARRIORS and hive.food >= constants.COST_WARRIOR:
                    hive.food -= constants.COST_WARRIOR
                    hive.warriors += 1
                elif action == constants.ACTION_PRODUCE_QUEEN and hive.food >= constants.COST_QUEEN and len(self.map.hives) < constants.MAX_HIVES:
                    spawn_loc = self._get_valid_spawn_location(hive)
                    if spawn_loc:
                        hive.food -= constants.COST_QUEEN
                        new_hive = Hive(self._next_hive_id, spawn_loc[0], spawn_loc[1], hive.faction)
                        self._next_hive_id += 1
                        new_queen = Queen(new_hive, self._next_queen_id)
                        self._next_queen_id += 1
                        new_hive.queens.append(new_queen)
                        self.map.hives.append(new_hive)
                
                # --- UPDATED: Advanced Combat Resolution ---
                elif action == constants.ACTION_ATTACK and hive.warriors > 0:
                    target = self._get_random_enemy_hive(hive.faction)
                    if target:
                        # Calculate raw power
                        attack_power = hive.warriors * hive.attack_multiplier
                        defense_power = target.warriors * target.defense_multiplier
                        
                        log_entry = f"--> COMBAT: Hive {hive.hive_id} ({attack_power} Pwr) attacked Hive {target.hive_id} ({defense_power} Pwr)!"
                        hive.diaries.append(log_entry)
                        
                        if attack_power >= defense_power:
                            # Attackers break the defense
                            surviving_power = attack_power - defense_power
                            target.warriors = 0
                            
                            # Convert surviving power back to raw units (round up)
                            surviving_attackers = math.ceil(surviving_power / hive.attack_multiplier)
                            
                            if surviving_attackers >= target.workers:
                                target.workers = 0
                                target.is_destroyed = True 
                            else:
                                target.workers -= surviving_attackers
                            
                            hive.warriors = surviving_attackers 
                        else:
                            # Defenders hold the line
                            surviving_power = defense_power - attack_power
                            
                            # Convert surviving power back to defending units
                            target.warriors = math.ceil(surviving_power / target.defense_multiplier)
                            hive.warriors = 0
                queen.action_queued = None

            if not hive.is_destroyed:
                hive.food += int(hive.workers * constants.GATHER_RATE_BASE * hive.gathering_modifier)

        self.map.hives = [h for h in self.map.hives if not h.is_destroyed]
        self.turn_number += 1