from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="Mi API-gotchi PWA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ESTADO DE LA MASCOTA ---
mascota = {
    "nombre": "Pixel",
    "hambre": 50,
    "felicidad": 50,
    "energia": 100,
    "estado": "vivo"
}

# --- ENDPOINTS DE LA API ---
@app.get("/estado")
def ver_mascota():
    return {"data": mascota}

@app.post("/alimentar")
def alimentar():
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Tu mascota no puede comer ahora.")
    mascota["hambre"] = max(0, mascota["hambre"] - 20)
    mascota["energia"] = max(0, mascota["energia"] - 5)
    return {"mensaje": "Le diste de comer a Pixel. ¡Ñam ñam!", "data": mascota}

@app.post("/jugar")
def jugar():
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Tu mascota no puede jugar ahora.")
    if mascota["energia"] < 20:
        raise HTTPException(status_code=400, detail="Pixel está muy cansado para jugar. Necesita dormir.")
    mascota["felicidad"] = min(100, mascota["felicidad"] + 15)
    mascota["energia"] = max(0, mascota["energia"] - 25)
    mascota["hambre"] = min(100, mascota["hambre"] + 10)
    if mascota["hambre"] == 100:
        mascota["estado"] = "fallecido"
        return {"mensaje": "Oh no... Pixel jugó demasiado, le dio mucha hambre y falleció.", "data": mascota}
    return {"mensaje": "¡Pixel se divirtió mucho!", "data": mascota}

@app.post("/dormir")
def dormir():
    if mascota["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Ya está descansando en paz.")
    mascota["energia"] = 100
    mascota["hambre"] = min(100, mascota["hambre"] + 15)
    return {"mensaje": "Pixel tomó una buena siesta. Zzz...", "data": mascota}

@app.post("/reiniciar")
def reiniciar():
    """Devuelve a la mascota a la vida con sus stats iniciales."""
    mascota["hambre"] = 50
    mascota["felicidad"] = 50
    mascota["energia"] = 100
    mascota["estado"] = "vivo"
    return {"mensaje": "¡Un milagro celestial! Pixel ha reencarnado. ✨", "data": mascota}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")