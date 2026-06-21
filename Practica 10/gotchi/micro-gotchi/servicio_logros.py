from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MS Logros")

estadisticas = {"jugadas": 0, "comidas": 0, "dormidas": 0}
medallas = []

class Accion(BaseModel):
    tipo: str # "jugar", "comer", "dormir"

@app.post("/auditar")
def registrar_accion(accion: Accion):
    nuevo_logro = None
    
    if accion.tipo == "jugar":
        estadisticas["jugadas"] += 1
        if estadisticas["jugadas"] == 3 and "Gamer Novato 🎮" not in medallas:
            nuevo_logro = "Gamer Novato 🎮"
            medallas.append(nuevo_logro)
            
    elif accion.tipo == "comer":
        estadisticas["comidas"] += 1
        if estadisticas["comidas"] == 3 and "Glotón 🍔" not in medallas:
            nuevo_logro = "Glotón 🍔"
            medallas.append(nuevo_logro)

    elif accion.tipo == "dormir":
        estadisticas["dormidas"] += 1
        if estadisticas["dormidas"] == 3 and "Dormilón 😴" not in medallas:
            nuevo_logro = "Dormilón 😴"
            medallas.append(nuevo_logro)

    return {"estadisticas": estadisticas, "medallas": medallas, "nuevo_logro": nuevo_logro}

@app.get("/estadisticas")
def ver_estadisticas():
    return {"estadisticas": estadisticas, "medallas": medallas}

@app.post("/reiniciar")
def reiniciar_logros():
    estadisticas.update({"jugadas": 0, "comidas": 0, "dormidas": 0})
    medallas.clear()
    return {"mensaje": "Logros reiniciados"}