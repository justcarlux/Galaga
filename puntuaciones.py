import json
import os

ARCHIVO_HIGHSCORES = "highscores.json"

def guardar_score(nombre, puntos):
    scores = []
    # 1. Intentar cargar scores existentes
    if os.path.exists(ARCHIVO_HIGHSCORES):
        try:
            with open(ARCHIVO_HIGHSCORES, "r") as f:
                scores = json.load(f)
        except:
            scores = []

    # 2. Lógica para evitar duplicados de nombre
    usuario_encontrado = False
    for item in scores:
        if item["nombre"] == nombre:
            usuario_encontrado = True
            # Solo actualizamos si el nuevo puntaje es mayor
            if puntos > item["puntos"]:
                item["puntos"] = puntos
            break
    
    # 3. Si el usuario no existía, lo añadimos
    if not usuario_encontrado:
        scores.append({"nombre": nombre, "puntos": puntos})

    # 4. Ordenar de mayor a menor
    scores.sort(key=lambda x: x["puntos"], reverse=True)
    
    # 5. Guardar solo los mejores 5
    with open(ARCHIVO_HIGHSCORES, "w") as f:
        json.dump(scores[:5], f, indent=4)

def obtener_highscores():
    if not os.path.exists(ARCHIVO_HIGHSCORES):
        return []
    try:
        with open(ARCHIVO_HIGHSCORES, "r") as f:
            datos = json.load(f)
            return [f"{item['nombre']} - {item['puntos']}" for item in datos]
    except:
        return []