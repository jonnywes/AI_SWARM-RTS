# ui.py
import pygame
import constants
import pyperclip

class UIManager:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("LLM RTS - MVP")
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        
        self.font_main = pygame.font.SysFont('Consolas', 14)
        self.font_large = pygame.font.SysFont('Consolas', 18, bold=True)
        self.font_title = pygame.font.SysFont('Consolas', 48, bold=True)
        
        self.input_text = ""
        self.input_rect = pygame.Rect(
            constants.MAP_WIDTH + 10, constants.SCREEN_HEIGHT - constants.INPUT_BOX_HEIGHT, 
            constants.TERMINAL_WIDTH - 20, constants.INPUT_BOX_HEIGHT - 10
        )
        self.input_active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        
        self.ollama_btn_rect = pygame.Rect(constants.MAP_WIDTH + 10, constants.SCREEN_HEIGHT - constants.INPUT_BOX_HEIGHT - 45, constants.TERMINAL_WIDTH - 20, 35)
        self.autoplay_btn_rect = pygame.Rect(constants.MAP_WIDTH + 10, constants.SCREEN_HEIGHT - constants.INPUT_BOX_HEIGHT - 85, constants.TERMINAL_WIDTH - 20, 35)
        self.ollama_btn_hover = False
        self.autoplay_btn_hover = False

        # --- Image Loading with Fallbacks ---
        try:
            self.img_bg = pygame.image.load("background.png").convert()
            self.img_bg = pygame.transform.scale(self.img_bg, (constants.MAP_WIDTH, constants.SCREEN_HEIGHT))
        except:
            self.img_bg = None

        try:
            self.img_hive_blue = pygame.image.load("blue_hive.png").convert_alpha()
            self.img_hive_blue = pygame.transform.scale(self.img_hive_blue, (64, 64))
        except:
            self.img_hive_blue = None

        try:
            self.img_hive_red = pygame.image.load("red_hive.png").convert_alpha()
            self.img_hive_red = pygame.transform.scale(self.img_hive_red, (64, 64))
        except:
            self.img_hive_red = None

    def handle_events(self, events):
        submitted_text = None
        action_signal = None
        
        mouse_pos = pygame.mouse.get_pos()
        self.ollama_btn_hover = self.ollama_btn_rect.collidepoint(mouse_pos)
        self.autoplay_btn_hover = self.autoplay_btn_rect.collidepoint(mouse_pos)
        
        for event in events:
            if event.type == pygame.QUIT:
                return "QUIT", None
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.ollama_btn_rect.collidepoint(event.pos):
                        action_signal = "OLLAMA_CLICK"
                    elif self.autoplay_btn_rect.collidepoint(event.pos):
                        action_signal = "AUTOPLAY_TOGGLE"
                        
                    if self.input_rect.collidepoint(event.pos):
                        self.input_active = True
                    else:
                        self.input_active = False
                
            if event.type == pygame.KEYDOWN and self.input_active:
                if event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL or event.mod & pygame.KMOD_META):
                    paste_text = pyperclip.paste()
                    if paste_text:
                        self.input_text += paste_text
                elif event.key == pygame.K_RETURN:
                    submitted_text = self.input_text
                    self.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                else:
                    if event.unicode and event.unicode.isprintable():
                        self.input_text += event.unicode
                        
        return submitted_text, action_signal

    # Update the draw method signature to accept active_instruction
    def draw(self, engine, prompt_message, error_message="", is_generating=False, auto_play=False, active_instruction=""):
        self.screen.fill(constants.COLOR_BG_MAP)
        self._draw_map(engine)
        self._draw_terminal(prompt_message, error_message, engine, is_generating, auto_play, active_instruction)
        pygame.display.flip()

    def _draw_map(self, engine):
        # Draw Image Background or fallback color
        if self.img_bg:
            self.screen.blit(self.img_bg, (0, 0))
        else:
            pygame.draw.rect(self.screen, constants.COLOR_BG_MAP, (0, 0, constants.MAP_WIDTH, constants.SCREEN_HEIGHT))

        turn_surface = self.font_large.render(f"TURN: {engine.turn_number} | TOTAL HIVES: {len(engine.map.hives)}/{constants.MAX_HIVES}", True, constants.COLOR_TEXT)
        self.screen.blit(turn_surface, (20, 20))
        
        for hive in engine.map.hives:
            # Render Hive Sprite or fallback square
            if hive.faction == constants.FACTION_PLAYER:
                if self.img_hive_blue: self.screen.blit(self.img_hive_blue, (hive.x, hive.y))
                else: pygame.draw.rect(self.screen, constants.COLOR_HIVE_BLUE, (hive.x, hive.y, 40, 40))
                id_label = f"HIVE {hive.hive_id} (BLUE)"
            else:
                if self.img_hive_red: self.screen.blit(self.img_hive_red, (hive.x, hive.y))
                else: pygame.draw.rect(self.screen, constants.COLOR_HIVE_RED, (hive.x, hive.y, 40, 40))
                id_label = f"HIVE {hive.hive_id} (RED)"
            
            current_obj = hive.queens[0].objective if hive.queens else "Dead"
            obj_text = self.font_main.render(f"[{current_obj}]", True, (200, 200, 50))
            
            id_text = self.font_main.render(id_label, True, constants.COLOR_HIGHLIGHT)
            food_text = self.font_main.render(f"Food: {hive.food}", True, constants.COLOR_TEXT)
            pop_text = self.font_main.render(f"Wkr:{hive.workers} War:{hive.warriors}", True, constants.COLOR_TEXT)
            
            self.screen.blit(obj_text, (hive.x, hive.y - 60))
            self.screen.blit(id_text, (hive.x, hive.y - 45))
            self.screen.blit(food_text, (hive.x, hive.y - 30))
            self.screen.blit(pop_text, (hive.x, hive.y - 15))

    # Update _draw_terminal signature and add the text box labels
    def _draw_terminal(self, prompt_message, error_message, engine, is_generating, auto_play, active_instruction):
        terminal_rect = pygame.Rect(constants.MAP_WIDTH, 0, constants.TERMINAL_WIDTH, constants.SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, constants.COLOR_BG_TERMINAL, terminal_rect)
        pygame.draw.line(self.screen, constants.COLOR_HIGHLIGHT, (constants.MAP_WIDTH, 0), (constants.MAP_WIDTH, constants.SCREEN_HEIGHT), 2)

        y_offset = 20
        
        if is_generating:
            display_prompt = "Hive Mind is thinking... (Please wait)"
            prompt_color = (255, 200, 50) 
        else:
            display_prompt = prompt_message
            prompt_color = constants.COLOR_HIGHLIGHT
            
        prompt_surface = self.font_large.render(display_prompt, True, prompt_color)
        self.screen.blit(prompt_surface, (constants.MAP_WIDTH + 10, y_offset))
        y_offset += 30

        if error_message:
            error_surface = self.font_main.render(error_message, True, (255, 100, 100))
            self.screen.blit(error_surface, (constants.MAP_WIDTH + 10, y_offset))
            y_offset += 25

        y_offset += 10
        recent_diaries = []
        for hive in engine.map.hives:
            recent_diaries.extend(hive.diaries)
        
        for log in recent_diaries[-5:]:
            for line in log.split('\n'):
                log_surface = self.font_main.render(line, True, constants.COLOR_TEXT)
                self.screen.blit(log_surface, (constants.MAP_WIDTH + 10, y_offset))
                y_offset += 15
            y_offset += 10

        if is_generating:
            btn_color = (100, 100, 100) 
        else:
            btn_color = constants.COLOR_HIGHLIGHT if self.ollama_btn_hover else (80, 120, 80)
        pygame.draw.rect(self.screen, btn_color, self.ollama_btn_rect)
        btn_text = self.font_large.render("Ask Hive Mind (Ollama)", True, (10, 10, 10))
        self.screen.blit(btn_text, btn_text.get_rect(center=self.ollama_btn_rect.center))

        ap_color = (50, 200, 255) if auto_play else (100, 100, 100)
        if self.autoplay_btn_hover and not auto_play: ap_color = (120, 120, 120)
        pygame.draw.rect(self.screen, ap_color, self.autoplay_btn_rect)
        ap_text_str = "AUTO-PLAY: ON" if auto_play else "AUTO-PLAY: OFF"
        ap_text = self.font_large.render(ap_text_str, True, (10, 10, 10))
        self.screen.blit(ap_text, ap_text.get_rect(center=self.autoplay_btn_rect.center))

        # --- FEATURE 2: ADVISOR UI LABELS ---
        # Draw the "Active Instruction" label above the input box
        instruction_label = "Current Advice: " + (active_instruction if active_instruction else "None (Type below)")
        inst_surface = self.font_main.render(instruction_label, True, (255, 200, 50))
        self.screen.blit(inst_surface, (self.input_rect.x, self.input_rect.y - 25))

        # Draw Input Box Background
        pygame.draw.rect(self.screen, constants.COLOR_INPUT_BG, self.input_rect)
        border_color = constants.COLOR_HIGHLIGHT if self.input_active else (80, 80, 80)
        pygame.draw.rect(self.screen, border_color, self.input_rect, 2)
        self._draw_multiline_text_with_cursor(self.input_text, self.input_rect.x + 5, self.input_rect.y + 5, self.input_rect.width - 10)
    def _draw_multiline_text_with_cursor(self, text, x, y, max_width):
        words = text.replace('\n', ' \n ').split(' ')
        lines = []
        current_line = ""
        for word in words:
            if word == '\n':
                lines.append(current_line)
                current_line = ""
                continue
            test_line = current_line + word + " "
            if self.font_main.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word + " "
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            text_surface = self.font_main.render(line, True, constants.COLOR_TEXT)
            self.screen.blit(text_surface, (x, y + (i * 18)))

        if self.input_active:
            self.cursor_timer += 1
            if self.cursor_timer >= constants.FPS // 2:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
            if self.cursor_visible:
                cursor_x = x + self.font_main.size(lines[-1])[0]
                cursor_y = y + ((len(lines) - 1) * 18)
                cursor_surface = self.font_main.render("_", True, constants.COLOR_HIGHLIGHT)
                self.screen.blit(cursor_surface, (cursor_x, cursor_y))
        else:
            self.cursor_timer = 0
            self.cursor_visible = True

    def draw_end_screen(self, message, sub_message="Close the window to exit."):
        self.screen.fill((20, 20, 20))
        
        color = constants.COLOR_HIGHLIGHT if "VICTORY" in message else (255, 50, 50)
        
        text_surface = self.font_title.render(message, True, color)
        sub_text = self.font_large.render(sub_message, True, constants.COLOR_TEXT)
        
        text_rect = text_surface.get_rect(center=(constants.SCREEN_WIDTH//2, constants.SCREEN_HEIGHT//2 - 20))
        sub_rect = sub_text.get_rect(center=(constants.SCREEN_WIDTH//2, constants.SCREEN_HEIGHT//2 + 30))
        
        self.screen.blit(text_surface, text_rect)
        self.screen.blit(sub_text, sub_rect)
        pygame.display.flip()