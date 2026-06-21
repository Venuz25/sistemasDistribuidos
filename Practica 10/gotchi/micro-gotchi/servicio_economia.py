from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MS Economía")

banco = {"monedas": 0}

class Transaccion(BaseModel):
    monto: int # Puede ser positivo (ganancia) o negativo (gasto)

@app.get("/cartera")
def ver_cartera():
    return banco

@app.post("/transaccion")
def procesar_transaccion(t: Transaccion):
    # Si es un gasto, verificamos si hay fondos suficientes
    if t.monto < 0 and banco["monedas"] + t.monto < 0:
        raise HTTPException(status_code=402, detail="Fondos insuficientes. ¡Ve a jugar para ganar monedas!")
    
    banco["monedas"] += t.monto
    return banco

@app.post("/reiniciar")
def reiniciar_economia():
    banco["monedas"] = 0
    return banco