# llm_api.py
import threading
import requests
import constants
import os

MEMORY_FILE = "memory.txt"
JOURNAL_FILE = "journal.txt"

class OllamaConnector:
    def __init__(self, model_name="llama3"): 
        self.model_name = model_name
        self.url = "http://localhost:11434/api/generate"
        
        self.is_generating = False
        self.response_data = None
        self.error_message = None
        
        self.is_analyzing = False
        self.post_mortem_done = False
        self.ancestral_memory = self._load_memory()
        self.journal = self._load_journal()

    def _load_memory(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "r") as f:
                return f.read().strip()
        else:
            default_memory = "- No prior memories. Focus on gathering food early to build a defense."
            with open(MEMORY_FILE, "w") as f:
                f.write(default_memory)
            return default_memory
        
    def _load_journal(self):
        # --- FEATURE 1: Clear the journal on startup ---
        default_journal = "Journal initialized. I must awaken and learn quickly to survive.\n"
        with open(JOURNAL_FILE, "w") as f: # 'w' ensures it wipes old data
            f.write(default_journal)
        return default_journal

    def _save_memory(self, new_memory):
        with open(MEMORY_FILE, "w") as f:
            f.write(new_memory)
        self.ancestral_memory = new_memory
    
    def add_journal_entry(self, turn, hive_id, queen_id, remarks):
        timestamp = f"Turn {turn} | Hive {hive_id} | Queen {queen_id}"
        log_entry = f"{timestamp}\nEntry: {remarks}\n\n"
        
        with open(JOURNAL_FILE, "a") as f:
            f.write(log_entry)
            
        self.journal += log_entry

    def generate_prompt(self, queen, engine, user_instructions=""):
        enemy_hives = sum(1 for h in engine.map.hives if h.faction == constants.FACTION_ENEMY)
        enemy_warriors = sum(h.warriors for h in engine.map.hives if h.faction == constants.FACTION_ENEMY)

        recent_logs = queen.hive.diaries[-5:]
        if recent_logs:
            short_term_memory = "\n\n".join(recent_logs)
        else:
            short_term_memory = "No previous actions. The Hive has just awakened."

        # --- FEATURE 2: Inject Advisor Instructions ---
        advisor_block = ""
        if user_instructions:
            advisor_block = f"\nTHE ADVISOR SPEAKS (Follow this guidance):\n{user_instructions}\n"

        prompt = f"""WARNING: Your response is being read by a Pygame parser. Follow these guidelines strictly.

You are a Hive Mind. You set Objectives for your Queens, and they will run autonomously to execute your will.
{advisor_block}
ANCESTRAL MEMORY:
{self.ancestral_memory}

LONG-TERM JOURNAL (Your history across this match):
{self.journal}

RECENT THOUGHTS (Last 5 turns for this specific Hive):
{short_term_memory}

CURRENT GAME STATE:
Awaiting orders for Queen {queen.queen_id}.
Hive {queen.hive.hive_id} Stats:
- Food: {queen.hive.food} | Workers: {queen.hive.workers} | Warriors: {queen.hive.warriors}
- Current Objective: {queen.objective}

THREAT REPORT:
- Known Enemy Hives: {enemy_hives}
- Total Enemy Warriors Spotted: {enemy_warriors}

VALID ACTIONS (You MUST set exactly ONE objective. DO NOT output micro-commands like 'Produce Workers'):
* {constants.ACTION_SET_OBJ_BALANCED} (Queen will build an equal mix of workers and warriors, attacking when her army is large.)
* {constants.ACTION_SET_OBJ_AGGRESSIVE} (Queen will halt economy, aggressively pump out warriors, and send frequent attacks.)
* {constants.ACTION_SET_OBJ_ECONOMY} (Queen will ignore military, build massive worker populations, and rapidly spawn new Hives.)

REQUIRED OUTPUT FORMAT:
TARGET UNIT: QUEEN
ACTION: [Insert exactly one valid action]
REMARKS: [Your diary. State your grand strategy here.]
"""
        return prompt

    def _make_request(self, prompt):
        self.is_generating = True
        self.response_data = None
        self.error_message = None
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}
        
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.response_data = data.get("response", "")
        except Exception as e:
            self.error_message = f"Ollama Connection Error: {str(e)}"
        finally:
            self.is_generating = False

    def request_action(self, queen, engine, user_instructions=""):
        if self.is_generating: return 
        # Pass the instructions down to the generator
        prompt = self.generate_prompt(queen, engine, user_instructions)
        thread = threading.Thread(target=self._make_request, args=(prompt,))
        thread.daemon = True 
        thread.start()

    # ... [post_mortem functions remain exactly the same] ...
    def _make_post_mortem_request(self, prompt):
        self.is_analyzing = True
        payload = {"model": self.model_name, "prompt": prompt, "stream": False}
        try:
            response = requests.post(self.url, json=payload)
            response.raise_for_status()
            data = response.json()
            new_memory = data.get("response", "").strip()
            self._save_memory(new_memory)
        except Exception as e:
            print(f"Post-Mortem Error: {str(e)}")
        finally:
            self.is_analyzing = False
            self.post_mortem_done = True

    def run_post_mortem(self, engine, is_victory):
        if self.is_analyzing or self.post_mortem_done: return
        turn_count = engine.turn_number
        outcome = "VICTORY" if is_victory else "DEFEAT"
        pm_prompt = f"""You are a Hive Mind AI that just finished playing a strategy game.
OUTCOME: {outcome}
Turns Lasted: {turn_count}

PREVIOUS ANCESTRAL MEMORY:
{self.ancestral_memory}

Write a new, updated Ancestral Memory in 3 bullet points or less detailing what strategy worked and what you should do differently next time to win faster or avoid dying. 
Keep it concise. Do not include any introductory or concluding text, ONLY output the bullet points."""
        thread = threading.Thread(target=self._make_post_mortem_request, args=(pm_prompt,))
        thread.daemon = True 
        thread.start()