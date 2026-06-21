from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="MS Inventario")

# Catálogo maestro de la tienda
catalogo = {
    "pizza": {"precio": 30, "efecto": {"hambre": -40, "energia": -5, "felicidad": 10}},
    "cafe": {"precio": 15, "efecto": {"hambre": 0, "energia": 30, "felicidad": 0}},
    "juguete": {"precio": 20, "efecto": {"hambre": 10, "energia": -15, "felicidad": 40}}
}

@app.get("/catalogo")
def ver_catalogo():
    return catalogo

@app.get("/item/{nombre_item}")
def obtener_info_item(nombre_item: str):
    if nombre_item not in catalogo:
        raise HTTPException(status_code=404, detail="Ese artículo no existe.")
    return catalogo[nombre_item]