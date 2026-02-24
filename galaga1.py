import pygame
import sys
import random
import math
import os
import puntuaciones 
import menu 

# --- CONFIGURACIÓN ---
width, height = 1040, 700

# 1. PRE-INICIALIZAR el audio con buffer mínimo (256) para latencia cero
pygame.mixer.pre_init(44100, -16, 2, 256)
pygame.init()
pygame.mixer.init() 

# 2. CARGAR Y REPRODUCIR MÚSICA DE INMEDIATO (Antes de cargar imágenes)
try:
    pygame.mixer.music.load("sonidos/ambiente.mpeg")
    pygame.mixer.music.set_volume(0.4)
    pygame.mixer.music.play(-1)
except: 
    pass

screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Space Adventure - ColorFusion")
clock = pygame.time.Clock()

black, white, red, green, yellow, cyan = (0,0,0), (255,255,255), (255,50,50), (0,255,0), (255,255,0), (0,255,255)

# --- FUENTES ---
def get_font(size):
    return pygame.font.SysFont("Impact", size)

# --- CARGA DE ASSETS ---
try:
    fondo = pygame.image.load("imagenes/fondo.webp").convert()
    fondo = pygame.transform.scale(fondo, (width, height))
except:
    fondo = pygame.Surface((width, height)); fondo.fill((10, 10, 30))

# Ejecutar menú (La música ya estará sonando)
menu.ejecutar_menu(screen, fondo)

# --- SONIDOS ---
def cargar_sonido(archivo):
    ruta = os.path.join("sonidos", archivo)
    try: return pygame.mixer.Sound(ruta)
    except: return None

snd_shoot = cargar_sonido("shoot.mpeg")
snd_kill_player = cargar_sonido("kill 3.mpeg")
snd_kill_alien = [cargar_sonido("kill 1.mpeg"), cargar_sonido("kill 2.mpeg")]
snd_stage = cargar_sonido("stage.mpeg")
snd_puntuacion = cargar_sonido("puntuacion.mpeg")
snd_start = cargar_sonido("start.mpeg")

rutas_aliens = ["aliens/alien 1.png", "aliens/alien 2.png", "aliens/alien3.png", "aliens/alien 4.png", "aliens/alien 5.png"]

def cargar_img(path, size, color):
    try:
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)
    except:
        s = pygame.Surface(size); s.fill(color); return s

# --- CLASES ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = cargar_img("imagenes/nave.png", (60, 60), green)
        self.rect = self.image.get_rect(centerx=width//2, bottom=height-10)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0: self.rect.x -= 8
        if keys[pygame.K_RIGHT] and self.rect.right < width: self.rect.x += 8

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, es_enemigo=False):
        super().__init__()
        self.image = pygame.Surface((5, 15))
        self.image.fill(red if es_enemigo else yellow)
        self.rect = self.image.get_rect(centerx=x, y=y)
        self.mask = pygame.mask.from_surface(self.image)
        self.speedy = 4 if es_enemigo else -12
    def update(self, *args):
        self.rect.y += self.speedy
        if self.rect.bottom < 0 or self.rect.top > height: self.kill()

class Meteor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = cargar_img("imagenes/asteroide.jpeg", (100, 100), (120, 120, 120))
        self.rect = self.image.get_rect(x=random.randint(0, width-100), y=-125)
        self.speedy = random.randint(1, 3) 
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args):
        self.rect.y += self.speedy
        if self.rect.top > height: self.kill()

class Alien1(pygame.sprite.Sprite):
    def __init__(self, x_rel, y_f, delay, lado, ruta, vidas=1):
        super().__init__()
        self.vidas = vidas
        self.image = cargar_img(ruta, (45, 45), red)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = -100 if lado == "izq" else width + 100
        self.px, self.py = float(self.rect.x), float(height // 2)
        self.x_rel, self.target_y, self.delay = x_rel, y_f, delay
        self.estado = "ENTRANDO"
        self.angle, self.radio = 0.0, 200.0

    def update(self, ancla_x):
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
            if random.random() < 0.001: disparar(self.rect.centerx, self.rect.bottom, True)
        elif self.estado == "ATACANDO":
            self.rect.y += 10
            if self.rect.bottom >= height: self.estado = "REGRESANDO"
        elif self.estado == "REGRESANDO":
            dx, dy = ancla_x + self.x_rel, self.target_y
            cx, cy = float(self.rect.x), float(self.rect.y)
            cx += (dx - cx) * 0.08
            cy += (dy - cy) * 0.08
            self.rect.x, self.rect.y = int(cx), int(cy)
            if math.hypot(dx - cx, dy - cy) < 2: self.estado = "ALINEADO"

class Boss(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.vidas = 200
        self.image = cargar_img("aliens/boss.png", (280, 200), (150, 0, 255))
        self.rect = self.image.get_rect(centerx=width//2, y=60)
        self.mask = pygame.mask.from_surface(self.image)
        self.speedx = 5
        self.last_spawn = pygame.time.get_ticks()
        self.last_shot = pygame.time.get_ticks()

    def update(self, *args):
        self.rect.x += self.speedx
        if self.rect.right > width or self.rect.left < 0: self.speedx *= -1
        ahora = pygame.time.get_ticks()
        if ahora - self.last_spawn > 10000:
            self.last_spawn = ahora
            for i in range(5):
                a = Alien1((i-2)*80, self.rect.bottom + 20, 0, "izq", rutas_aliens[0])
                a.estado = "ALINEADO"
                alien_group.add(a); all_sprites.add(a)
        if ahora - self.last_shot > 3000:
            if random.random() < 0.4:
                for dx in [-80, 0, 80]: 
                    disparar(self.rect.centerx + dx, self.rect.bottom, True)
                self.last_shot = ahora

# --- FUNCIONES ---
def ingresar_nombre(puntos):
    if snd_puntuacion: snd_puntuacion.play()
    nombre = ""
    font_title, font_input = get_font(50), get_font(40)
    running = True
    while running:
        screen.fill(black)
        txt = font_title.render(f"PUNTOS: {puntos}", True, yellow)
        prompt = font_input.render("ESCRIBE TU NOMBRE:", True, white)
        nom_txt = font_input.render(nombre + "_", True, green)
        screen.blit(txt, (width//2 - txt.get_width()//2, 150))
        screen.blit(prompt, (width//2 - prompt.get_width()//2, 250))
        screen.blit(nom_txt, (width//2 - nom_txt.get_width()//2, 350))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and nombre != "":
                    puntuaciones.guardar_score(nombre, puntos); running = False
                elif event.key == pygame.K_BACKSPACE: nombre = nombre[:-1]
                else:
                    if len(nombre) < 10 and event.unicode.isalnum():
                        nombre += event.unicode.upper()

def disparar(x, y, enemigo=False):
    b = Bullet(x, y, enemigo)
    all_sprites.add(b)
    if enemigo: enemy_bullets.add(b)
    else: 
        player_bullets.add(b)
        if snd_shoot: snd_shoot.play()

def cargar_nivel(n):
    if n > 1 and snd_stage: snd_stage.play()
    alien_group.empty(); boss_group.empty(); meteors.empty(); all_sprites.empty()
    player_bullets.empty(); enemy_bullets.empty()
    all_sprites.add(player)
    if n == 8:
        b = Boss(); boss_group.add(b); all_sprites.add(b)
    else:
        v = 2 if n == 7 else 1
        for f in range(5):
            ruta_actual = rutas_aliens[f % len(rutas_aliens)]
            for c in range(10):
                a = Alien1(c*80 - 360, 80+f*60, f*40+c*5, "izq", ruta_actual, v)
                alien_group.add(a); all_sprites.add(a)

def seleccionar_stage(n):
    global stage, ancla_x, game_over, score
    stage = n
    if n == 1: score = 0
    if snd_start: snd_start.play()
    ancla_x = width // 2
    game_over = False
    player.rect.centerx = width // 2
    cargar_nivel(stage)

# --- INICIALIZACIÓN ---
player = Player()
all_sprites, alien_group = pygame.sprite.Group(), pygame.sprite.Group()
player_bullets, enemy_bullets = pygame.sprite.Group(), pygame.sprite.Group()
meteors, boss_group = pygame.sprite.Group(), pygame.sprite.Group()

stage, ancla_x, dir_f, game_over, score = 1, width//2, 1, False, 0
fuente_hud = get_font(30)
seleccionar_stage(1)

# --- BUCLE PRINCIPAL ---
while True:
    clock.tick(60)
    screen.blit(fondo, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if event.type == pygame.KEYDOWN:
            if not game_over:
                if event.key == pygame.K_SPACE: disparar(player.rect.centerx, player.rect.top)
            else:
                if pygame.K_1 <= event.key <= pygame.K_8:
                    seleccionar_stage(event.key - pygame.K_0)

    if not game_over:
        if 4 <= stage <= 6 and random.random() < 0.02:
            if len(meteors) < 5: 
                m = Meteor(); meteors.add(m); all_sprites.add(m)

        if stage < 8:
            ancla_x += 4 * dir_f
            if ancla_x > width - 420 or ancla_x < 420: dir_f *= -1
            if random.random() < 0.01:
                listos = [a for a in alien_group if a.estado == "ALINEADO"]
                if listos: random.choice(listos).estado = "ATACANDO"
        else:
            if len(boss_group) > 0: ancla_x = boss_group.sprites()[0].rect.centerx

        # COLISIONES
        if pygame.sprite.spritecollide(player, alien_group, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(player, enemy_bullets, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(player, meteors, False, pygame.sprite.collide_mask) or \
           pygame.sprite.spritecollide(player, boss_group, False, pygame.sprite.collide_mask):
            if snd_kill_player: snd_kill_player.play()
            game_over = True
            ingresar_nombre(score)

        for b in player_bullets:
            for a in pygame.sprite.spritecollide(b, alien_group, False, pygame.sprite.collide_mask):
                a.vidas -= 1; b.kill()
                if a.vidas <= 0: 
                    a.kill(); score += 10
                    if snd_kill_alien: random.choice(snd_kill_alien).play()
            if pygame.sprite.spritecollide(b, meteors, True, pygame.sprite.collide_mask):
                score += 5; b.kill()
                if snd_kill_alien: snd_kill_alien[0].play()
            for boss in pygame.sprite.spritecollide(b, boss_group, False, pygame.sprite.collide_mask):
                boss.vidas -= 1; b.kill()
                if boss.vidas <= 0: 
                    boss.kill(); score += 500
                    if snd_kill_alien: snd_kill_alien[1].play()

        player.update()
        player_bullets.update(); enemy_bullets.update(); meteors.update()
        boss_group.update(); alien_group.update(ancla_x)

        if len(alien_group) == 0 and len(boss_group) == 0:
            stage += 1; cargar_nivel(stage)

    all_sprites.draw(screen)
    screen.blit(fuente_hud.render(f"STAGE: {stage}  SCORE: {score}", True, white), (20, 20))
    if stage == 8 and len(boss_group) > 0:
        vida_boss = boss_group.sprites()[0].vidas
        screen.blit(fuente_hud.render(f"BOSS HP: {vida_boss}", True, red), (width-200, 20))

    if game_over:
        font_big, font_inst = get_font(80), get_font(35)
        msg = font_big.render("GAME OVER", True, red)
        screen.blit(msg, (width//2-msg.get_width()//2, height//2-180))
        highs = puntuaciones.obtener_highscores()
        for i, h in enumerate(highs):
            h_txt = fuente_hud.render(f"{i+1}. {h}", True, cyan)
            screen.blit(h_txt, (width//2-h_txt.get_width()//2, height//2 - 60 + i*30))
        inst_txt = font_inst.render("PRESIONA UN NUMERO (1-8) PARA VOLVER A EMPEZAR", True, yellow)
        screen.blit(inst_txt, (width//2-inst_txt.get_width()//2, height - 80))

    pygame.display.flip()