from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Mi API-gotchi", description="Cuida a tu mascota virtual por API")

# Estado inicial de nuestra mascota
mascota = {
    "nombre": "Pixel",
    "hambre": 50,      # 0 es lleno, 100 es inanición
    "felicidad": 50,   # 0 es triste, 100 es súper feliz
    "energia": 100,    # 0 es exhausto, 100 es descansado
    "estado": "vivo"
}

# --- ENDPOINTS ---

@app.get("/")
def ver_mascota():
    """Devuelve el estado actual de tu API-gotchi."""
    return mascota

@app.post("/alimentar")
def alimentar():
    """Alimentar a la mascota reduce su hambre, pero da un poco de sueño."""
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Tu mascota no puede comer ahora.")
    
    mascota["hambre"] = max(0, mascota["hambre"] - 20)
    mascota["energia"] = max(0, mascota["energia"] - 5)
    return {"mensaje": "Le diste de comer a Pixel. ¡Ñam ñam!", "estado": mascota}

@app.post("/jugar")
def jugar():
    """Jugar aumenta la felicidad, pero gasta energía y da hambre."""
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Tu mascota no puede jugar ahora.")
    
    if mascota["energia"] < 20:
        return {"mensaje": "Pixel está muy cansado para jugar. Necesita dormir."}

    mascota["felicidad"] = min(100, mascota["felicidad"] + 15)
    mascota["energia"] = max(0, mascota["energia"] - 25)
    mascota["hambre"] = min(100, mascota["hambre"] + 10)
    
    # Lógica de "Game Over"
    if mascota["hambre"] == 100:
        mascota["estado"] = "fallecido"
        return {"mensaje": "Oh no... Pixel jugó demasiado, le dio mucha hambre y falleció.", "estado": mascota}

    return {"mensaje": "¡Pixel se divirtió mucho!", "estado": mascota}

@app.post("/dormir")
def dormir():
    """Dormir recupera energía al máximo, pero da un poco de hambre."""
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Ya está descansando en paz.")
    
    mascota["energia"] = 100
    mascota["hambre"] = min(100, mascota["hambre"] + 15)
    return {"mensaje": "Pixel tomó una buena siesta. Zzz...", "estado": mascota}