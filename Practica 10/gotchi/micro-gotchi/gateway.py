from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import httpx

app = FastAPI(title="API Gateway Maestro")

# Direcciones de nuestra red de microservicios
URLs = {
    "vitales": "http://127.0.0.1:8001",
    "economia": "http://127.0.0.1:8002",
    "inventario": "http://127.0.0.1:8003",
    "logros": "http://127.0.0.1:8004"
}

async def obtener_estado_interno(client: httpx.AsyncClient):
    r_vit = await client.get(f"{URLs['vitales']}/vitales")
    r_eco = await client.get(f"{URLs['economia']}/cartera")
    r_logros = await client.get(f"{URLs['logros']}/estadisticas")
    
    estado = r_vit.json()
    estado["monedas"] = r_eco.json()["monedas"]
    estado["medallas"] = r_logros.json()["medallas"]
    estado["estadisticas"] = r_logros.json()["estadisticas"]
    return estado

@app.get("/estado")
async def estado_general():
    async with httpx.AsyncClient() as client:
        try:
            estado = await obtener_estado_interno(client)
            return {"data": estado}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Red de microservicios inestable.")

@app.post("/jugar")
async def accion_jugar():
    async with httpx.AsyncClient() as client:
        try:
            # 1. Validar si puede jugar y aplicar desgaste (Vitales)
            r_vit = await client.post(f"{URLs['vitales']}/modificar", json={"hambre": 10, "energia": -25, "felicidad": 15})
            if r_vit.status_code != 200: raise HTTPException(status_code=400, detail=r_vit.json().get("detail"))

            # 2. Recompensa económica (Economía)
            await client.post(f"{URLs['economia']}/transaccion", json={"monto": 20})
            
            # 3. Auditar acción para posibles trofeos (Logros)
            r_logro = await client.post(f"{URLs['logros']}/auditar", json={"tipo": "jugar"})
            
            mensaje = "¡Jugó y ganó 20 monedas! 💰"
            nuevo_logro = r_logro.json().get("nuevo_logro")
            if nuevo_logro:
                mensaje += f" ¡NUEVO LOGRO DESBLOQUEADO: {nuevo_logro}!"

            estado = await obtener_estado_interno(client)
            return {"mensaje": mensaje, "data": estado}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Error de comunicación interna.")

@app.post("/comprar/{item}")
async def accion_comprar_y_usar(item: str):
    async with httpx.AsyncClient() as client:
        try:
            # 1. Consultar Inventario para saber precio y efecto
            r_inv = await client.get(f"{URLs['inventario']}/item/{item}")
            if r_inv.status_code != 200: raise HTTPException(status_code=404, detail="Ítem no encontrado.")
            info_item = r_inv.json()

            # 2. Intentar cobrar en Economía
            r_pago = await client.post(f"{URLs['economia']}/transaccion", json={"monto": -info_item["precio"]})
            if r_pago.status_code != 200: raise HTTPException(status_code=402, detail=r_pago.json().get("detail"))

            # 3. Aplicar efecto en Vitales
            await client.post(f"{URLs['vitales']}/modificar", json=info_item["efecto"])

            # 4. Auditar (Contar como comida)
            r_logro = await client.post(f"{URLs['logros']}/auditar", json={"tipo": "comer"})
            
            mensaje = f"Compraste y consumiste {item.upper()}."
            nuevo_logro = r_logro.json().get("nuevo_logro")
            if nuevo_logro: mensaje += f" ¡NUEVO LOGRO: {nuevo_logro}!"

            # OBTENER ESTADO ACTUALIZADO PARA EL FRONTEND
            estado = await obtener_estado_interno(client)
            return {"mensaje": mensaje, "data": estado}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Error de comunicación interna.")
        
@app.post("/dormir")
async def accion_dormir():
    async with httpx.AsyncClient() as client:
        try:
            # 1. Modificar vitales
            r_vit = await client.post(f"{URLs['vitales']}/modificar", json={"hambre": 15, "energia": 100, "felicidad": 0})
            if r_vit.status_code != 200: raise HTTPException(status_code=400, detail=r_vit.json().get("detail"))
            
            # 2. Auditar la acción en el microservicio de Logros
            r_logro = await client.post(f"{URLs['logros']}/auditar", json={"tipo": "dormir"})

            mensaje = "Pixel durmió profundamente. Zzz..."
            nuevo_logro = r_logro.json().get("nuevo_logro")
            if nuevo_logro: mensaje += f" ¡NUEVO LOGRO: {nuevo_logro}!"

            estado = await obtener_estado_interno(client)
            return {"mensaje": mensaje, "data": estado, "nuevo_logro": nuevo_logro}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Error de comunicación interna.")

@app.post("/reiniciar")
async def accion_reiniciar():
    async with httpx.AsyncClient() as client:
        try:
            await client.post(f"{URLs['vitales']}/reiniciar")
            await client.post(f"{URLs['economia']}/reiniciar")
            await client.post(f"{URLs['logros']}/reiniciar")
            
            # OBTENER ESTADO ACTUALIZADO PARA EL FRONTEND
            estado = await obtener_estado_interno(client)
            return {"mensaje": "Reseteo global de la red.", "data": estado}
        except httpx.ConnectError:
            raise HTTPException(status_code=503, detail="Error de comunicación interna.")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")