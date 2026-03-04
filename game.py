import pygame
import sys
import random
import math
from pathlib import Path
from arcade_machine_sdk import GameBase, BASE_WIDTH, BASE_HEIGHT

# Importar módulos auxiliares
import menu
try:
    import puntuaciones
except ImportError:
    class puntuaciones:
        @staticmethod
        def guardar_score(n, p): pass
        @staticmethod
        def obtener_highscores(): return []

# --- CONFIGURACIÓN DE RUTAS ---
GAME_DIR = Path(__file__).resolve().parent
IMAGES_DIR = GAME_DIR / "imagenes"
SOUNDS_DIR = GAME_DIR / "sonidos"
ALIENS_DIR = GAME_DIR / "aliens"
FONT_PATH = GAME_DIR / "PressStart2P-Regular.ttf"

# --- COLORES ---
BLACK, WHITE, RED, GREEN, YELLOW, CYAN = (0,0,0), (255,255,255), (255,50,50), (0,255,0), (255,255,0), (0,255,255)

def load_image(path, size, fallback_color):
    try:
        img = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        s = pygame.Surface(size)
        s.fill(fallback_color)
        return s

def load_sound(file):
    try:
        return pygame.mixer.Sound(str(SOUNDS_DIR / file))
    except:
        return None

def get_font(size):
    try:
        return pygame.font.Font(str(FONT_PATH), size)
    except:
        return pygame.font.SysFont("Impact", size)

# --- CLASES DEL JUEGO ---

class Player(pygame.sprite.Sprite):
    def __init__(self, width, height):
        super().__init__()
        self.width, self.height = width, height
        self.image = load_image(IMAGES_DIR / "nave.png", (60, 60), GREEN)
        self.rect = self.image.get_rect(centerx=width//2, bottom=height-10)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= 8
        if keys[pygame.K_RIGHT] and self.rect.right < self.width: self.rect.x += 8

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, height, es_enemigo=False):
        super().__init__()
        self.height = height
        self.image = pygame.Surface((5, 15))
        self.image.fill(RED if es_enemigo else YELLOW)
        self.rect = self.image.get_rect(centerx=x, y=y)
        self.mask = pygame.mask.from_surface(self.image)
        self.speedy = 4 if es_enemigo else -12
    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0 or self.rect.top > self.height: self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self, width, height):
        super().__init__()
        self.width, self.height = width, height
        self.image = load_image(IMAGES_DIR / "asteroide.png", (100, 100), (120, 120, 120))
        self.rect = self.image.get_rect(x=random.randint(0, width-100), y=-125)
        self.speedy = random.randint(1, 3)
        self.mask = pygame.mask.from_surface(self.image)
    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > self.height: self.kill()

class Alien1(pygame.sprite.Sprite):
    def __init__(self, x_rel, y_f, delay, lado, ruta, width, height, vidas=1):
        super().__init__()
        self.width, self.height = width, height
        self.vidas = vidas
        self.image = load_image(ruta, (45, 45), RED)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = -100 if lado == "izq" else width + 100
        self.px, self.py = float(self.rect.x), float(height // 2)
        self.x_rel, self.target_y, self.delay = x_rel, y_f, delay
        self.estado = "ENTRANDO"
        self.angle, self.radio = 0.0, 200.0

    def update(self, ancla_x, disparar_func):
        if self.delay > 0: self.delay -= 1; return
        if self.estado == "ENTRANDO":
            self.angle += 0.15
            if self.radio > 0: self.radio -= 3.0
            dest_x = ancla_x + self.x_rel
            self.px += (dest_x - self.px) * 0.1
            self.py += (self.target_y - self.py) * 0.1
            self.rect.x = int(self.px + math.cos(self.angle) * self.radio)
            self.rect.y = int(self.py + math.sin(self.angle) * self.radio)
            if self.radio <= 0 and abs(dest_x - self.px) < 2: self.estado = "ALINEADO"
        elif self.estado == "ALINEADO":
            self.rect.x, self.rect.y = int(ancla_x + self.x_rel), self.target_y
            if random.random() < 0.001: disparar_func(self.rect.centerx, self.rect.bottom, True)
        elif self.estado == "ATACANDO":
            self.rect.y += 10
            if self.rect.bottom >= self.height: self.estado = "REGRESANDO"
        elif self.estado == "REGRESANDO":
            dx, dy = ancla_x + self.x_rel, self.target_y
            cx, cy = float(self.rect.x), float(self.rect.y)
            cx += (dx - cx) * 0.08
            cy += (dy - cy) * 0.08
            self.rect.x, self.rect.y = int(cx), int(cy)
            if math.hypot(dx - cx, dy - cy) < 2: self.estado = "ALINEADO"

class Boss(pygame.sprite.Sprite):
    def __init__(self, width, height, rutas_aliens, alien_group, all_sprites, disparar_func):
        super().__init__()
        self.width, self.height = width, height
        self.rutas_aliens = rutas_aliens
        self.alien_group = alien_group
        self.all_sprites = all_sprites
        self.disparar = disparar_func
        self.vidas = 200
        self.image = load_image(ALIENS_DIR / "boss.png", (280, 200), (150, 0, 255))
        self.rect = self.image.get_rect(centerx=width//2, y=60)
        self.mask = pygame.mask.from_surface(self.image)
        self.speedx = 5
        self.last_spawn = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()

    def update(self):
        self.rect.x += self.speedx
        if self.rect.right > self.width or self.rect.left < 0: self.speedx *= -1
        ahora = pygame.time.get_ticks()
        if ahora - self.last_spawn > 10000:
            self.last_spawn = ahora
            for i in range(5):
                a = Alien1((i-2)*80, self.rect.bottom + 20, 0, "izq", self.rutas_aliens[0], self.width, self.height)
                a.estado = "ALINEADO"
                self.alien_group.add(a)
                self.all_sprites.add(a)
        if ahora - self.last_shot > 3000:
            if random.random() < 0.4:
                for dx in [-80, 0, 80]: 
                    self.disparar(self.rect.centerx + dx, self.rect.bottom, True)
                self.last_shot = ahora

# --- CLASE PRINCIPAL ---

class GalagaGame(GameBase):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.state = "MENU" 
        self.game_over = False
        self.width, self.height = BASE_WIDTH, BASE_HEIGHT
        if not pygame.get_init(): pygame.init()
        if not pygame.mixer.get_init(): pygame.mixer.init()
        self.fondo = load_image(IMAGES_DIR / "fondo.png", (self.width, self.height), (10, 10, 30))
        
        # Estrellas pre-calculadas para el fondo espacial
        self.stars = [(random.randint(0, self.width), random.randint(0, self.height)) for _ in range(100)]
        
        self.snd_shoot = load_sound("shoot.mpeg")
        self.snd_kill_player = load_sound("kill 3.mpeg")
        raw_sounds = [load_sound("kill 1.mpeg"), load_sound("kill 2.mpeg")]
        self.snd_kill_alien = [s for s in raw_sounds if s] 
        self.snd_stage = load_sound("stage.mpeg")
        self.snd_puntuacion = load_sound("puntuacion.mpeg")
        self.snd_start = load_sound("start.mpeg")
        self.rutas_aliens = [ALIENS_DIR / "alien 1.png", ALIENS_DIR / "alien 2.png", 
                             ALIENS_DIR / "alien3.png", ALIENS_DIR / "alien 4.png", 
                             ALIENS_DIR / "alien 5.png"]
        self.stage = 1
        self.reset_game_vars()

    def reset_game_vars(self):
        self.all_sprites = pygame.sprite.Group()
        self.alien_group = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.meteors = pygame.sprite.Group()
        self.boss_group = pygame.sprite.Group()
        self.player = Player(self.width, self.height)
        self.all_sprites.add(self.player)
        self.ancla_x = self.width // 2
        self.dir_f = 1
        self.nombre_input = ""
        self.game_over = False

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_8:
                    if self.state != "ENTER_NAME":
                        self.stage = event.key - pygame.K_0
                        self.reset_game_vars()
                        self.cargar_nivel(self.stage)
                        self.state = "PLAYING"

            if self.state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    btn_w, btn_h = 380, 85
                    start_y = 300
                    gap = 115
                    btn_play = pygame.Rect(self.width//2 - btn_w//2, start_y, btn_w, btn_h)
                    btn_score = pygame.Rect(self.width//2 - btn_w//2, start_y + gap, btn_w, btn_h)
                    btn_quit = pygame.Rect(self.width//2 - btn_w//2, start_y + gap*2, btn_w, btn_h)
                    if btn_play.collidepoint(event.pos):
                        self.state = "PLAYING"
                        self.stage = 1
                        self.score = 0
                        self.reset_game_vars()
                        self.cargar_nivel(self.stage)
                        if self.snd_start: self.snd_start.play()
                    elif btn_score.collidepoint(event.pos): self.state = "SCORES"
                    elif btn_quit.collidepoint(event.pos):
                        self.stop()

            elif self.state == "SCORES":
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    self.state = "MENU"

            elif self.state == "PLAYING":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.disparar(self.player.rect.centerx, self.player.rect.top, False)

            elif self.state == "ENTER_NAME":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.state = "MENU"
                    elif event.key == pygame.K_RETURN and self.nombre_input != "":
                        puntuaciones.guardar_score(self.nombre_input, self.score)
                        self.state = "GAME_OVER"
                    elif event.key == pygame.K_BACKSPACE: self.nombre_input = self.nombre_input[:-1]
                    else:
                        if len(self.nombre_input) < 10 and event.unicode.isalnum():
                            self.nombre_input += event.unicode.upper()

            elif self.state == "GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    self.state = "MENU"
                elif event.type == pygame.MOUSEBUTTONDOWN: self.state = "MENU"

    def update(self, dt):
        if self.state != "PLAYING" or self.game_over: return
        
        if 4 <= self.stage <= 6 and random.random() < 0.02:
            if len(self.meteors) < 5: 
                m = Meteor(self.width, self.height)
                self.meteors.add(m); self.all_sprites.add(m)
        
        if self.stage < 8:
            self.ancla_x += 4 * self.dir_f
            if self.ancla_x > self.width - 420 or self.ancla_x < 420: self.dir_f *= -1
            if random.random() < 0.01:
                listos = [a for a in self.alien_group if a.estado == "ALINEADO"]
                if listos: random.choice(listos).estado = "ATACANDO"
        else:
            if len(self.boss_group) > 0: self.ancla_x = self.boss_group.sprites()[0].rect.centerx

        if pygame.sprite.spritecollide(self.player, self.alien_group, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(self.player, self.enemy_bullets, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(self.player, self.meteors, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(self.player, self.boss_group, False, pygame.sprite.collide_mask):
            if self.snd_kill_player: self.snd_kill_player.play()
            self.game_over = True; self.state = "ENTER_NAME"
            if self.snd_puntuacion: self.snd_puntuacion.play()

        for b in self.player_bullets:
            for a in pygame.sprite.spritecollide(b, self.alien_group, False, pygame.sprite.collide_mask):
                a.vidas -= 1; b.kill()
                if a.vidas <= 0: 
                    a.kill(); self.score += 10
                    if self.snd_kill_alien: random.choice(self.snd_kill_alien).play()
            if pygame.sprite.spritecollide(b, self.meteors, True, pygame.sprite.collide_mask):
                self.score += 5; b.kill()
                if self.snd_kill_alien: self.snd_kill_alien[0].play()
            for boss in pygame.sprite.spritecollide(b, self.boss_group, False, pygame.sprite.collide_mask):
                boss.vidas -= 1; b.kill()
                if boss.vidas <= 0: 
                    boss.kill(); self.score += 500
                    if self.snd_kill_alien: self.snd_kill_alien[-1].play()

        self.player.update(); self.player_bullets.update(); self.enemy_bullets.update()
        self.meteors.update(); self.boss_group.update()
        for alien in self.alien_group: alien.update(self.ancla_x, self.disparar)
        
        if len(self.alien_group) == 0 and len(self.boss_group) == 0:
            self.stage += 1
            self.cargar_nivel(self.stage)

    def render(self, surface=None):
        if surface is None:
            try: surface = self._GameBase__surface
            except AttributeError: return
            
        # --- LÓGICA DE FONDO DINÁMICA ---
        if self.state == "MENU" or self.state == "SCORES":
            surface.blit(self.fondo, (0, 0))
        else:
            # Dibujar espacio profundo negro con estrellas
            surface.fill(BLACK)
            for star in self.stars:
                pygame.draw.circle(surface, WHITE, star, 1)
        
        if self.state == "MENU": menu.draw_menu(surface, pygame.mouse.get_pos())
        elif self.state == "SCORES": menu.draw_highscores(surface)
        elif self.state in ["PLAYING", "ENTER_NAME", "GAME_OVER"]:
            self.all_sprites.draw(surface)
            
            f_hud = get_font(20)
            hud_txt = f"STAGE:{self.stage} SCORE:{self.score}"
            surface.blit(f_hud.render(hud_txt, True, WHITE), (20, 20))
            
            if self.stage == 8 and len(self.boss_group) > 0:
                v_b = self.boss_group.sprites()[0].vidas
                surface.blit(f_hud.render(f"BOSS HP:{v_b}", True, RED), (self.width-280, 20))
            
            if self.state == "ENTER_NAME":
                s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                s.fill((0,0,0,220)); surface.blit(s, (0,0))
                f_t, f_i = get_font(30), get_font(18)
                surface.blit(f_t.render(f"PUNTOS: {self.score}", True, YELLOW), (self.width//2-180, 150))
                surface.blit(f_i.render("ESCRIBE NOMBRE Y ENTER:", True, WHITE), (self.width//2-230, 250))
                surface.blit(f_i.render(self.nombre_input + "_", True, GREEN), (self.width//2-50, 320))

            elif self.state == "GAME_OVER":
                f_b, f_inst = get_font(50), get_font(18)
                msg = f_b.render("GAME OVER", True, RED)
                surface.blit(msg, (self.width//2-msg.get_width()//2, self.height//2-180))
                
                esc_msg = f_inst.render("ESC: VOLVER AL MENU", True, WHITE)
                surface.blit(esc_msg, (self.width//2 - esc_msg.get_width()//2, self.height - 80))
                
                try:
                    highs = puntuaciones.obtener_highscores()
                    for i, h in enumerate(highs[:5]):
                        h_txt = f_inst.render(f"{i+1}. {h}", True, CYAN)
                        surface.blit(h_txt, (self.width//2-h_txt.get_width()//2, self.height//2 - 20 + i*40))
                except: pass

    def disparar(self, x, y, enemigo=False):
        b = Bullet(x, y, self.height, enemigo)
        self.all_sprites.add(b)
        if enemigo: self.enemy_bullets.add(b)
        else: 
            self.player_bullets.add(b)
            if self.snd_shoot: self.snd_shoot.play()

    def cargar_nivel(self, n):
        if n > 1 and self.snd_stage: self.snd_stage.play()
        self.alien_group.empty(); self.boss_group.empty(); self.meteors.empty(); 
        for s in self.all_sprites.sprites():
            if s != self.player: s.kill()
        self.player_bullets.empty(); self.enemy_bullets.empty()
        self.game_over = False; self.ancla_x = self.width // 2
        self.player.rect.centerx = self.width // 2
        
        if n == 8:
            b = Boss(self.width, self.height, self.rutas_aliens, self.alien_group, self.all_sprites, self.disparar)
            self.boss_group.add(b); self.all_sprites.add(b)
        else:
            v = 2 if n == 7 else 1
            for f in range(5):
                ruta_actual = self.rutas_aliens[f % len(self.rutas_aliens)]
                for c in range(10):
                    a = Alien1(c*80 - 360, 80+f*60, f*40+c*5, "izq", ruta_actual, self.width, self.height, v)
                    self.alien_group.add(a); self.all_sprites.add(a)

    def start(self, surface):
        super().start(surface)
        try:
            pygame.mixer.music.load(str(SOUNDS_DIR / "ambiente.mpeg"))
            pygame.mixer.music.set_volume(0.4)
            pygame.mixer.music.play(-1)
        except: pass

    def stop(self):
        super().stop()
        pygame.mixer.music.stop()