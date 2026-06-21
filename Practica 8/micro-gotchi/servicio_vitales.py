from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MS Vitales")

# Base de datos en memoria del servicio
estado_vital = {
    "nombre": "Pixel", "hambre": 50, "felicidad": 50, "energia": 100, "estado": "vivo"
}

class DeltasVitales(BaseModel):
    hambre: int = 0
    felicidad: int = 0
    energia: int = 0

@app.get("/vitales")
def obtener_vitales():
    return estado_vital

@app.post("/modificar")
def modificar_vitales(deltas: DeltasVitales):
    if estado_vital["estado"] != "vivo":
        raise HTTPException(status_code=400, detail="Pixel ya no está con nosotros.")

    # Aplicamos los cambios (deltas) asegurando límites de 0 a 100
    estado_vital["hambre"] = max(0, min(100, estado_vital["hambre"] + deltas.hambre))
    estado_vital["felicidad"] = max(0, min(100, estado_vital["felicidad"] + deltas.felicidad))
    estado_vital["energia"] = max(0, min(100, estado_vital["energia"] + deltas.energia))
    
    if estado_vital["hambre"] == 100:
        estado_vital["estado"] = "fallecido"

    return estado_vital

@app.post("/reiniciar")
def reiniciar_vitales():
    estado_vital.update({"hambre": 50, "felicidad": 50, "energia": 100, "estado": "vivo"})
    return estado_vital