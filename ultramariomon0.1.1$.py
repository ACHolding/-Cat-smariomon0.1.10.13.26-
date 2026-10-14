# program.py
# Cat's Mariomon Engine v0.1
# 60 FPS | speed = "gba" | Native 240x160 GBA Resolution (3x Integer Scale)
# Inspired by Super Mariomon (GBA ROM Hack)

import math
import random
import sys
import pygame

# --- ENGINE & GBA HARDWARE CONFIGURATION ---
ENGINE_NAME = "Cat's Mariomon Engine v0.1"
speed = "gba"
FPS = 60  # GBA hardware refresh rate (~59.7275 Hz / 60 FPS)
GBA_WIDTH, GBA_HEIGHT = 240, 160
SCALE = 3
WINDOW_WIDTH, WINDOW_HEIGHT = GBA_WIDTH * SCALE, GBA_HEIGHT * SCALE
TILE_SIZE = 16  # 15x10 visible tiles on a 240x160 GBA screen

# GBA Pokemon Emerald movement speeds (pixels per frame at 60 FPS)
GBA_WALK_SPEED = 1  # 16 frames per tile (~0.26s)
GBA_RUN_SPEED = 2  # 8 frames per tile (~0.13s, hold X / Shift)

# GBA 15-bit Inspired Color Palette
C_SKY = (104, 184, 248)
C_GRASS = (88, 200, 80)
C_GRASS_DARK = (56, 160, 56)
C_TALL_GRASS = (32, 136, 48)
C_PATH = (232, 208, 144)
C_PATH_EDGE = (200, 176, 112)
C_BLOCK = (248, 184, 0)
C_BLOCK_SHADOW = (184, 112, 0)
C_PIPE = (0, 176, 0)
C_PIPE_LIGHT = (88, 232, 72)
C_MARIO_RED = (240, 40, 40)
C_MARIO_BLUE = (40, 80, 232)
C_SKIN = (248, 200, 144)
C_WHITE = (248, 248, 248)
C_BLACK = (24, 24, 24)
C_UI_BG = (248, 248, 216)
C_UI_BORDER = (56, 64, 88)
C_HP_GREEN = (72, 208, 80)
C_HP_YELLOW = (248, 208, 0)
C_HP_RED = (240, 56, 40)

# Map Legend:
# 0 = Grass, 1 = Tall Grass (Wild Encounters), 2 = Toad Road, 3 = ? Block (Wall), 4 = Warp Pipe (Heal)
WORLD_MAP = [
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    [3, 0, 0, 1, 1, 1, 0, 2, 0, 1, 1, 1, 0, 4, 3],
    [3, 0, 3, 1, 1, 1, 0, 2, 0, 1, 1, 1, 0, 0, 3],
    [3, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 3],
    [3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    [3, 0, 0, 0, 1, 1, 0, 2, 0, 3, 0, 3, 0, 0, 3],
    [3, 0, 4, 0, 1, 1, 0, 2, 0, 0, 0, 0, 1, 1, 3],
    [3, 0, 0, 0, 1, 1, 0, 2, 0, 1, 1, 1, 1, 1, 3],
    [3, 0, 0, 0, 0, 0, 0, 2, 0, 1, 1, 1, 1, 1, 3],
    [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3],
]

WILD_DATABASE = [
    {
        "name": "GOOMBA",
        "lv": 5,
        "max_hp": 24,
        "atk": 7,
        "color": (168, 88, 32),
        "move": "Headbonk",
    },
    {
        "name": "KOOPA TROOPA",
        "lv": 6,
        "max_hp": 28,
        "atk": 8,
        "color": (48, 184, 48),
        "move": "Shell Toss",
    },
    {
        "name": "SHY GUY",
        "lv": 7,
        "max_hp": 30,
        "atk": 9,
        "color": (232, 48, 64),
        "move": "Slingshot",
    },
    {
        "name": "BOO",
        "lv": 8,
        "max_hp": 26,
        "atk": 11,
        "color": (224, 224, 248),
        "move": "Spook",
    },
    {
        "name": "MINI BOWSER",
        "lv": 10,
        "max_hp": 42,
        "atk": 13,
        "color": (216, 120, 0),
        "move": "Fire Breath",
    },
]


class CatsMariomonEngine:

    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"{ENGINE_NAME} | 60 FPS | speed={speed}")
        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.gba_surface = pygame.Surface((GBA_WIDTH, GBA_HEIGHT))
        self.clock = pygame.time.Clock()

        # Retro pixel-friendly fonts
        self.font_sm = pygame.font.SysFont("courier", 10, bold=True)
        self.font_md = pygame.font.SysFont("courier", 12, bold=True)
        self.font_lg = pygame.font.SysFont("courier", 15, bold=True)

        # Speed & Frame Tracking
        self.speed_mult = 1 if speed == "gba" else 2
        self.frame_count = 0

        # Game State: "TITLE", "OVERWORLD", "TRANSITION", "BATTLE"
        self.state = "TITLE"
        self.transition_timer = 0

        # Player Grid & Pixel Position (Tile 7, 4 center road)
        self.grid_x, self.grid_y = 7, 4
        self.px, self.py = (
            self.grid_x * TILE_SIZE,
            self.grid_y * TILE_SIZE,
        )
        self.target_px, self.target_py = self.px, self.py
        self.moving = False
        self.move_step = GBA_WALK_SPEED
        self.facing = "DOWN"

        # Player Party & Inventory
        self.party = [
            {
                "name": "LUIGIMON",
                "lv": 8,
                "hp": 36,
                "max_hp": 36,
                "atk": 11,
                "color": (40, 184, 64),
                "move": "Green Fireball",
            }
        ]
        self.capballs = 5
        self.mushrooms = 3
        self.overworld_msg = ""
        self.overworld_msg_timer = 0

        # Battle State Variables
        self.enemy = None
        self.battle_phase = (
            "MESSAGE"  # "MENU", "MESSAGE", "ENEMY_TURN", "END"
        )
        self.menu_cursor = 0  # 0: FIGHT, 1: CAPBALL, 2: SHROOM, 3: RUN
        self.battle_msg = ""
        self.msg_char_index = 0
        self.next_phase = "MENU"

    def set_battle_message(self, text, next_phase="MENU"):
        self.battle_msg = text
        self.msg_char_index = 0
        self.battle_phase = "MESSAGE"
        self.next_phase = next_phase

    # --- INPUT & UPDATE LOGIC ---
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # TAB cycles GBA Emulator Speed (1x Native -> 2x -> 4x)
                if event.key == pygame.K_TAB:
                    self.speed_mult = {1: 2, 2: 4, 4: 1}[self.speed_mult]

                if self.state == "TITLE":
                    if event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "OVERWORLD"
                        self.show_overworld_banner(
                            "Welcome to Mushroom Kingdom!"
                        )

                elif self.state == "BATTLE":
                    self.handle_battle_keydown(event.key)

    def handle_battle_keydown(self, key):
        if self.battle_phase == "MESSAGE":
            if key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                if self.msg_char_index < len(self.battle_msg):
                    self.msg_char_index = len(self.battle_msg)
                else:
                    if self.next_phase == "END":
                        self.state = "OVERWORLD"
                    elif self.next_phase == "ENEMY_TURN":
                        self.execute_enemy_turn()
                    else:
                        self.battle_phase = self.next_phase

        elif self.battle_phase == "MENU":
            if key in (pygame.K_RIGHT, pygame.K_d) and self.menu_cursor % 2 == 0:
                self.menu_cursor += 1
            elif (
                key in (pygame.K_LEFT, pygame.K_a) and self.menu_cursor % 2 == 1
            ):
                self.menu_cursor -= 1
            elif key in (pygame.K_DOWN, pygame.K_s) and self.menu_cursor < 2:
                self.menu_cursor += 2
            elif key in (pygame.K_UP, pygame.K_w) and self.menu_cursor >= 2:
                self.menu_cursor -= 2
            elif key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                self.execute_player_choice()

    def execute_player_choice(self):
        lead = self.party[0]
        if self.menu_cursor == 0:  # FIGHT
            dmg = max(
                2,
                lead["atk"] + random.randint(-2, 3) - (self.enemy["lv"] // 3),
            )
            self.enemy["hp"] = max(0, self.enemy["hp"] - dmg)
            if self.enemy["hp"] == 0:
                lead["lv"] += 1
                lead["max_hp"] += 3
                lead["hp"] = min(lead["max_hp"], lead["hp"] + 3)
                lead["atk"] += 1
                self.set_battle_message(
                    f"{lead['name']} used {lead['move']}! {self.enemy['name']} fainted! Lv Up!",
                    "END",
                )
            else:
                self.set_battle_message(
                    f"{lead['name']} used {lead['move']}! Dealt {dmg} DMG!",
                    "ENEMY_TURN",
                )

        elif self.menu_cursor == 1:  # CAPBALL
            if self.capballs <= 0:
                self.set_battle_message("No CapBalls left!", "MENU")
                return
            self.capballs -= 1
            hp_ratio = self.enemy["hp"] / self.enemy["max_hp"]
            catch_chance = 0.75 - (0.50 * hp_ratio)
            if random.random() < catch_chance:
                captured = dict(self.enemy)
                captured["hp"] = captured["max_hp"]
                self.party.append(captured)
                self.set_battle_message(
                    f"Gotcha! {self.enemy['name']} was caught! (Party: {len(self.party)})",
                    "END",
                )
            else:
                self.set_battle_message(
                    f"Oh no! Wild {self.enemy['name']} broke free!",
                    "ENEMY_TURN",
                )

        elif self.menu_cursor == 2:  # MUSHROOM
            if self.mushrooms <= 0:
                self.set_battle_message("Out of Super Mushrooms!", "MENU")
                return
            self.mushrooms -= 1
            heal = 18
            lead["hp"] = min(lead["max_hp"], lead["hp"] + heal)
            self.set_battle_message(
                f"Used Super Mushroom! Recovered {heal} HP!", "ENEMY_TURN"
            )

        elif self.menu_cursor == 3:  # RUN
            self.set_battle_message("Got away safely!", "END")

    def execute_enemy_turn(self):
        lead = self.party[0]
        dmg = max(1, self.enemy["atk"] + random.randint(-2, 2) - (lead["lv"] // 3))
        lead["hp"] = max(0, lead["hp"] - dmg)
        if lead["hp"] == 0:
            lead["hp"] = lead["max_hp"]
            self.grid_x, self.grid_y = 7, 4
            self.px = self.target_px = self.grid_x * TILE_SIZE
            self.py = self.target_py = self.grid_y * TILE_SIZE
            self.set_battle_message(
                f"{lead['name']} fainted! Warped back to Toad Road!", "END"
            )
        else:
            self.set_battle_message(
                f"Wild {self.enemy['name']} used {self.enemy['move']}! ({dmg} DMG)",
                "MENU",
            )

    def show_overworld_banner(self, text, frames=120):
        self.overworld_msg = text
        self.overworld_msg_timer = frames

    def update_overworld(self):
        if self.overworld_msg_timer > 0:
            self.overworld_msg_timer -= 1

        keys = pygame.key.get_pressed()
        running_shoes = keys[pygame.K_x] or keys[pygame.K_LSHIFT]

        if not self.moving:
            dx, dy = 0, 0
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                dy, self.facing = -1, "UP"
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                dy, self.facing = 1, "DOWN"
            elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
                dx, self.facing = -1, "LEFT"
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                dx, self.facing = 1, "RIGHT"

            if dx != 0 or dy != 0:
                nx, ny = self.grid_x + dx, self.grid_y + dy
                if 0 <= nx < 15 and 0 <= ny < 10 and WORLD_MAP[ny][nx] != 3:
                    self.grid_x, self.grid_y = nx, ny
                    self.target_px = nx * TILE_SIZE
                    self.target_py = ny * TILE_SIZE
                    self.moving = True
                    self.move_step = (
                        GBA_RUN_SPEED if running_shoes else GBA_WALK_SPEED
                    )
        else:
            # Step pixel-by-pixel at authentic GBA frame speed
            if self.px < self.target_px:
                self.px = min(self.target_px, self.px + self.move_step)
            elif self.px > self.target_px:
                self.px = max(self.target_px, self.px - self.move_step)

            if self.py < self.target_py:
                self.py = min(self.target_py, self.py + self.move_step)
            elif self.py > self.target_py:
                self.py = max(self.target_py, self.py - self.move_step)

            if self.px == self.target_px and self.py == self.target_py:
                self.moving = False
                tile = WORLD_MAP[self.grid_y][self.grid_x]
                if tile == 4:  # Warp Pipe Heal
                    for mon in self.party:
                        mon["hp"] = mon["max_hp"]
                    self.capballs = max(self.capballs, 5)
                    self.mushrooms = max(self.mushrooms, 3)
                    self.show_overworld_banner(
                        "Warp Pipe Restored Party & Items!"
                    )
                elif tile == 1 and random.random() < 0.18:  # Wild Encounter
                    self.trigger_wild_battle()

    def trigger_wild_battle(self):
        template = random.choice(WILD_DATABASE)
        self.enemy = dict(template)
        self.enemy["hp"] = self.enemy["max_hp"]
        self.state = "TRANSITION"
        self.transition_timer = 36
        self.menu_cursor = 0
        self.set_battle_message(f"Wild {self.enemy['name']} appeared!", "MENU")

    def update(self):
        self.frame_count += 1
        if self.state == "OVERWORLD":
            self.update_overworld()
        elif self.state == "TRANSITION":
            self.transition_timer -= 1
            if self.transition_timer <= 0:
                self.state = "BATTLE"
        elif self.state == "BATTLE":
            if self.battle_phase == "MESSAGE" and self.msg_char_index < len(
                self.battle_msg
            ):
                self.msg_char_index += 1

    # --- GBA RENDERING PIPELINE (240x160) ---
    def draw_title_screen(self, surf):
        surf.fill(C_SKY)
        # Ground hills & pipe
        pygame.draw.rect(surf, C_GRASS, (0, 128, GBA_WIDTH, 32))
        pygame.draw.rect(surf, C_GRASS_DARK, (0, 128, GBA_WIDTH, 4))
        pygame.draw.rect(surf, C_PIPE, (196, 100, 24, 28))
        pygame.draw.rect(surf, C_PIPE_LIGHT, (194, 96, 28, 6))

        # Banner Box
        pygame.draw.rect(surf, C_UI_BORDER, (16, 18, 208, 58), border_radius=4)
        pygame.draw.rect(surf, C_UI_BG, (19, 21, 202, 52), border_radius=3)

        t1 = self.font_md.render("CAT'S MARIOMON ENGINE", True, C_MARIO_RED)
        t2 = self.font_sm.render(
            "v0.1  |  GBA 60 FPS BUILD", True, C_MARIO_BLUE
        )
        t3 = self.font_sm.render("ROM Hack Recreation Core", True, C_BLACK)
        surf.blit(t1, (GBA_WIDTH // 2 - t1.get_width() // 2, 26))
        surf.blit(t2, (GBA_WIDTH // 2 - t2.get_width() // 2, 42))
        surf.blit(t3, (GBA_WIDTH // 2 - t3.get_width() // 2, 56))

        # Animated Bouncing Question Block & Mario
        bounce = int(abs(math.sin(self.frame_count * 0.08)) * 6)
        pygame.draw.rect(surf, C_BLOCK, (112, 86 - bounce, 16, 16))
        pygame.draw.rect(surf, C_BLOCK_SHADOW, (112, 86 - bounce, 16, 16), 1)
        q_mark = self.font_md.render("?", True, C_WHITE)
        surf.blit(q_mark, (116, 87 - bounce))

        self.draw_mario_sprite(surf, 84, 112)

        if (self.frame_count // 25) % 2 == 0:
            prompt = self.font_sm.render("PRESS Z OR ENTER TO START", True, C_BLACK)
            surf.blit(prompt, (GBA_WIDTH // 2 - prompt.get_width() // 2, 140))

    def draw_mario_sprite(self, surf, x, y):
        # 16x16 Procedural GBA Mario Overworld Sprite
        pygame.draw.rect(surf, C_MARIO_RED, (x + 3, y + 1, 10, 4))  # Cap
        pygame.draw.rect(surf, C_SKIN, (x + 4, y + 5, 8, 4))  # Face
        pygame.draw.rect(surf, C_MARIO_RED, (x + 3, y + 9, 10, 4))  # Shirt
        pygame.draw.rect(surf, C_MARIO_BLUE, (x + 4, y + 10, 8, 5))  # Overalls
        pygame.draw.rect(surf, C_BLACK, (x + 3, y + 14, 4, 2))  # Left Boot
        pygame.draw.rect(surf, C_BLACK, (x + 9, y + 14, 4, 2))  # Right Boot

    def draw_overworld(self, surf):
        for r in range(10):
            for c in range(15):
                x, y = c * TILE_SIZE, r * TILE_SIZE
                tile = WORLD_MAP[r][c]
                pygame.draw.rect(surf, C_GRASS, (x, y, TILE_SIZE, TILE_SIZE))

                if tile == 1:  # Tall Grass blades
                    pygame.draw.rect(
                        surf, C_TALL_GRASS, (x + 2, y + 3, 12, 11)
                    )
                    pygame.draw.line(
                        surf, C_GRASS, (x + 5, y + 3), (x + 5, y + 12), 1
                    )
                    pygame.draw.line(
                        surf, C_GRASS, (x + 10, y + 3), (x + 10, y + 12), 1
                    )
                elif tile == 2:  # Toad Road
                    pygame.draw.rect(surf, C_PATH, (x, y, TILE_SIZE, TILE_SIZE))
                    pygame.draw.rect(
                        surf, C_PATH_EDGE, (x, y, TILE_SIZE, TILE_SIZE), 1
                    )
                elif tile == 3:  # ? Block Wall
                    pygame.draw.rect(
                        surf, C_BLOCK, (x, y, TILE_SIZE, TILE_SIZE)
                    )
                    pygame.draw.rect(
                        surf, C_BLOCK_SHADOW, (x, y, TILE_SIZE, TILE_SIZE), 1
                    )
                    surf.blit(
                        self.font_sm.render("?", True, C_WHITE), (x + 5, y + 2)
                    )
                elif tile == 4:  # Warp Pipe
                    pygame.draw.rect(
                        surf, C_PIPE, (x + 2, y + 4, 12, 12)
                    )
                    pygame.draw.rect(
                        surf, C_PIPE_LIGHT, (x + 1, y + 1, 14, 4)
                    )

        self.draw_mario_sprite(surf, self.px, self.py)

        # Top HUD Bar (Engine Branding + Speed + Party Summary)
        pygame.draw.rect(surf, C_UI_BORDER, (0, 0, GBA_WIDTH, 14))
        lead = self.party[0]
        hud_text = (
            f"CAT'S MARIOMON v0.1 | {lead['name']} Lv{lead['lv']} "
            f"HP:{lead['hp']}/{lead['max_hp']} | {self.speed_mult}x GBA"
        )
        surf.blit(self.font_sm.render(hud_text, True, C_WHITE), (4, 1))

        if self.overworld_msg_timer > 0:
            pygame.draw.rect(surf, C_UI_BORDER, (8, 132, 224, 24))
            pygame.draw.rect(surf, C_UI_BG, (10, 134, 220, 20))
            surf.blit(
                self.font_sm.render(self.overworld_msg, True, C_BLACK),
                (16, 138),
            )

    def draw_hp_bar(self, surf, x, y, hp, max_hp):
        ratio = max(0.0, min(1.0, hp / max_hp))
        color = (
            C_HP_GREEN
            if ratio > 0.5
            else (C_HP_YELLOW if ratio > 0.2 else C_HP_RED)
        )
        pygame.draw.rect(surf, C_BLACK, (x, y, 52, 6))
        pygame.draw.rect(surf, color, (x + 1, y + 1, int(50 * ratio), 4))

    def draw_battle(self, surf):
        # Background Arena
        surf.fill((168, 224, 248))
        pygame.draw.ellipse(surf, (120, 208, 112), (128, 48, 96, 28))
        pygame.draw.ellipse(surf, (120, 208, 112), (12, 92, 104, 30))

        # Enemy Sprite & Status Box
        ex, ey = 160, 24
        pygame.draw.rect(
            surf, self.enemy["color"], (ex, ey, 32, 32), border_radius=6
        )
        pygame.draw.rect(surf, C_BLACK, (ex, ey, 32, 32), 2, border_radius=6)
        pygame.draw.rect(surf, C_WHITE, (ex + 6, ey + 8, 6, 8))
        pygame.draw.rect(surf, C_WHITE, (ex + 20, ey + 8, 6, 8))
        pygame.draw.rect(surf, C_BLACK, (ex + 8, ey + 10, 3, 5))
        pygame.draw.rect(surf, C_BLACK, (ex + 22, ey + 10, 3, 5))

        pygame.draw.rect(surf, C_UI_BORDER, (10, 10, 108, 34), border_radius=3)
        pygame.draw.rect(surf, C_UI_BG, (12, 12, 104, 30), border_radius=2)
        surf.blit(
            self.font_sm.render(
                f"{self.enemy['name']} Lv{self.enemy['lv']}", True, C_BLACK
            ),
            (16, 14),
        )
        self.draw_hp_bar(surf, 16, 28, self.enemy["hp"], self.enemy["max_hp"])

        # Player Mariomon Sprite & Status Box
        lead = self.party[0]
        px, py = 44, 74
        pygame.draw.rect(
            surf, lead["color"], (px, py, 34, 34), border_radius=5
        )
        pygame.draw.rect(surf, C_BLACK, (px, py, 34, 34), 2, border_radius=5)

        pygame.draw.rect(
            surf, C_UI_BORDER, (120, 68, 112, 40), border_radius=3
        )
        pygame.draw.rect(surf, C_UI_BG, (122, 70, 108, 36), border_radius=2)
        surf.blit(
            self.font_sm.render(
                f"{lead['name']} Lv{lead['lv']}", True, C_BLACK
            ),
            (126, 72),
        )
        self.draw_hp_bar(surf, 126, 86, lead["hp"], lead["max_hp"])
        surf.blit(
            self.font_sm.render(
                f"{lead['hp']}/{lead['max_hp']} HP", True, C_BLACK
            ),
            (182, 83),
        )

        # Bottom GBA Battle Dialog / Command Bar
        pygame.draw.rect(surf, C_UI_BORDER, (0, 112, GBA_WIDTH, 48))
        pygame.draw.rect(surf, C_UI_BG, (3, 115, GBA_WIDTH - 6, 42))

        if self.battle_phase == "MESSAGE":
            visible_text = self.battle_msg[: self.msg_char_index]
            surf.blit(
                self.font_sm.render(visible_text[:34], True, C_BLACK),
                (10, 122),
            )
            if len(visible_text) > 34:
                surf.blit(
                    self.font_sm.render(visible_text[34:68], True, C_BLACK),
                    (10, 136),
                )
        elif self.battle_phase == "MENU":
            surf.blit(
                self.font_sm.render("What will Mario do?", True, C_BLACK),
                (10, 124),
            )
            pygame.draw.rect(surf, C_UI_BORDER, (124, 114, 114, 44))
            pygame.draw.rect(surf, C_WHITE, (126, 116, 110, 40))

            options = [
                "FIGHT",
                f"CAP({self.capballs})",
                f"SHROOM({self.mushrooms})",
                "RUN",
            ]
            coords = [(134, 120), (184, 120), (134, 138), (184, 138)]
            for idx, label in enumerate(options):
                cx, cy = coords[idx]
                prefix = ">" if self.menu_cursor == idx else " "
                surf.blit(
                    self.font_sm.render(f"{prefix}{label}", True, C_BLACK),
                    (cx - 6, cy),
                )

    def render(self):
        if self.state == "TITLE":
            self.draw_title_screen(self.gba_surface)
        elif self.state == "OVERWORLD":
            self.draw_overworld(self.gba_surface)
        elif self.state == "TRANSITION":
            self.draw_overworld(self.gba_surface)
            if (self.transition_timer // 4) % 2 == 0:
                self.gba_surface.fill(C_WHITE)
        elif self.state == "BATTLE":
            self.draw_battle(self.gba_surface)

        # Scale native 240x160 GBA framebuffer to 720x480 window
        pygame.transform.scale(
            self.gba_surface, (WINDOW_WIDTH, WINDOW_HEIGHT), self.window
        )
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            for _ in range(self.speed_mult):
                self.update()
            self.render()
            self.clock.tick(FPS)


if __name__ == "__main__":
    engine = CatsMariomonEngine()
    engine.run()
