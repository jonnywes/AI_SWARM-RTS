# main.py
import pygame
import constants
from engine import GameEngine
from ui import UIManager
from parser import parse_llm_command
from llm_api import OllamaConnector

def main():
    engine = GameEngine()
    ui = UIManager()
    ollama = OllamaConnector(model_name="llama3") 
    clock = pygame.time.Clock()
    
    running = True
    error_message = ""
    
    auto_play_enabled = False
    game_over = False
    game_over_message = ""
    is_victory = False 
    
    # --- NEW: State Variables ---
    active_instruction = ""
    consecutive_errors = 0
    
    engine.start_turn()

    while running:
        if not game_over:
            player_hives = sum(1 for h in engine.map.hives if h.faction == constants.FACTION_PLAYER)
            enemy_hives = sum(1 for h in engine.map.hives if h.faction == constants.FACTION_ENEMY)
            
            if player_hives == 0:
                game_over = True
                is_victory = False
                game_over_message = "DEFEAT! The Hive Mind has been eradicated."
            elif enemy_hives == 0:
                game_over = True
                is_victory = True
                game_over_message = "VICTORY! The enemy has been consumed."
                
        if game_over:
            if not ollama.post_mortem_done and not ollama.is_analyzing:
                ollama.run_post_mortem(engine, is_victory)
            
            if ollama.is_analyzing:
                ui.draw_end_screen(game_over_message, sub_message="Writing new Ancestral Memory to file... Please wait.")
            else:
                ui.draw_end_screen(game_over_message, sub_message="Ancestral Memory saved. Close the window to exit.")
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            clock.tick(constants.FPS)
            continue

        prompt_message = ""
        current_queen = None
        
        if engine.active_queens_queue:
            current_queen = engine.active_queens_queue[0]
            prompt_message = f"Turn {engine.turn_number}: Awaiting orders for Queen {current_queen.queen_id} (Hive {current_queen.hive.hive_id})"
        else:
            engine.end_turn()
            engine.start_turn()
            error_message = "" 
            continue 

        # Handle UI Events
        submitted_text, action_signal = ui.handle_events(pygame.event.get())
        
        if submitted_text == "QUIT":
            running = False
            
        elif action_signal == "AUTOPLAY_TOGGLE":
            auto_play_enabled = not auto_play_enabled
            if auto_play_enabled:
                consecutive_errors = 0 # Reset strikes when turned on

        # --- FEATURE 2: Update the Advisor Instruction ---
        if submitted_text is not None:
            active_instruction = submitted_text.strip() # Set it to whatever the user hit Enter on

        # Trigger Ollama (Manual Click)
        if action_signal == "OLLAMA_CLICK" and current_queen and not ollama.is_generating:
            error_message = "" 
            ollama.request_action(current_queen, engine, active_instruction)

        # Trigger Ollama (Auto-Play)
        if auto_play_enabled and current_queen and not ollama.is_generating and not ollama.response_data:
            error_message = ""
            ollama.request_action(current_queen, engine, active_instruction)

        # Check for Ollama Thread Completion
        if ollama.response_data:
            parsed_data = parse_llm_command(ollama.response_data)
            
            if parsed_data["status"] == "success":
                consecutive_errors = 0 # --- FEATURE 3: Reset strikes on success ---
                
                ollama.add_journal_entry(
                    turn=engine.turn_number, 
                    hive_id=current_queen.hive.hive_id, 
                    queen_id=current_queen.queen_id, 
                    remarks=parsed_data["remarks"]
                )
                
                engine.process_queen_command(current_queen, parsed_data)
                engine.active_queens_queue.pop(0)
                error_message = ""
            else:
                error_message = parsed_data["message"]
                consecutive_errors += 1 # --- FEATURE 3: Add a strike ---
                
                print("\n" + "="*50)
                print(f"🚨 LLM ERROR (Strike {consecutive_errors}/3) 🚨")
                print("="*50)
                print(f"ERROR: {error_message}")
                print("RAW LLM OUTPUT:")
                print(parsed_data.get("raw_text", "No text returned."))
                print("="*50 + "\n")
                
                # --- FEATURE 3: Disable after 3 fails ---
                if consecutive_errors >= 3:
                    auto_play_enabled = False 
                    print("Auto-Play Disabled due to 3 consecutive failures.")
                
            ollama.response_data = None
            
        if ollama.error_message:
            error_message = ollama.error_message
            ollama.error_message = None
            auto_play_enabled = False

        # Render the Screen
        # Pass active_instruction so the UI can display it
        ui.draw(engine, prompt_message, error_message, is_generating=ollama.is_generating, auto_play=auto_play_enabled, active_instruction=active_instruction)
        
        clock.tick(constants.FPS)

    pygame.quit()

if __name__ == "__main__":
    main()