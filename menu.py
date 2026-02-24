import pygame
import sys
import os
import puntuaciones # Importamos para mostrar los scores

def ejecutar_menu(ventana, fondo_img_fallback):
    pygame.font.init()
    # Definimos los colores: Cyan para el estado normal y Brillo para selección
    BLANCO = (255, 255, 255)
    CYAN = (0, 255, 255)
    BRILLO = (255, 255, 0)

    # Intentar cargar fondo.jpeg
    try:
        fondo_menu = pygame.image.load("imagenes/fondo.jpeg").convert()
        fondo_menu = pygame.transform.scale(fondo_menu, (1040, 700))
    except:
        fondo_menu = fondo_img_fallback

    # Carga de fuentes
    try:
        fuente_inicio = pygame.font.Font("PressStart2P-Regular.ttf", 40)
        fuente_titulo = pygame.font.Font("PressStart2P-Regular.ttf", 100)
        fuente_score = pygame.font.SysFont("Impact", 35)
    except:
        fuente_inicio = pygame.font.SysFont("Impact", 50)
        fuente_titulo = pygame.font.SysFont("Impact", 110)
        fuente_score = pygame.font.SysFont("Arial", 35)

    boton_play = pygame.Rect(330, 300, 380, 85)
    boton_score = pygame.Rect(330, 415, 380, 85)
    boton_quit = pygame.Rect(330, 530, 380, 85)

    def mostrar_tabla_scores():
        """Sub-bucle para mostrar las puntuaciones"""
        while True:
            ventana.blit(fondo_menu, (0, 0))
            titulo_s = fuente_inicio.render("HIGHSCORES", True, BRILLO)
            ventana.blit(titulo_s, (520 - titulo_s.get_width()//2, 50))
            
            # Obtener y mostrar scores usando tu módulo puntuaciones.py
            lista_scores = puntuaciones.obtener_highscores()
            for i, score in enumerate(lista_scores):
                txt = fuente_score.render(f"{i+1}. {score}", True, BLANCO)
                ventana.blit(txt, (520 - txt.get_width()//2, 150 + i * 45))
            
            volver_txt = fuente_score.render("Presiona cualquier tecla para volver", True, CYAN)
            ventana.blit(volver_txt, (520 - volver_txt.get_width()//2, 600))
            
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    return # Sale de la tabla de scores y vuelve al menú

    def dibujar(mouse_pos):
        ventana.blit(fondo_menu, (0, 0))
        
        # Título en Blanco
        titulo = fuente_titulo.render("Galaga", True, BLANCO)
        ventana.blit(titulo, (520 - titulo.get_width()//2, 100))

        # Botones en Cyan
        for btn, txt in [(boton_play, "Play"), (boton_score, "Score"), (boton_quit, "Quit")]:
            # Cambia a Brillo si el mouse está encima
            col = BRILLO if btn.collidepoint(mouse_pos) else CYAN
            
            pygame.draw.rect(ventana, col, btn, 4, 35)
            t_render = fuente_inicio.render(txt, True, col)
            ventana.blit(t_render, (btn.centerx - t_render.get_width()//2, btn.y + 20))
        
        pygame.display.update()

    while True:
        m_pos = pygame.mouse.get_pos()
        dibujar(m_pos)
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_play.collidepoint(event.pos): 
                    return "PLAY"
                if boton_score.collidepoint(event.pos):
                    mostrar_tabla_scores() # Llama a la nueva función de puntuaciones
                if boton_quit.collidepoint(event.pos): 
                    pygame.quit(); sys.exit()