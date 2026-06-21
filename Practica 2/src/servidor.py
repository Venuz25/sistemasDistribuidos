import socket
import json
import sys

# Configuración del Servidor
HOST = '0.0.0.0'  # Escuchar en todas las interfaces disponibles
PORT = 65432      # Puerto estándar para el servicio

# Estructura: { "id_secreto": "datos_cifrados_en_base64" }
vault_storage = {}

def handle_client(conn, addr):
    """Maneja la comunicación con el cliente conectado."""
    print(f"[CONEXIÓN ESTABLECIDA] {addr} conectado.")
    connected = True
    
    while connected:
        try:
            # Recibir longitud del mensaje (Encabezado de 4 bytes)
            msg_length = conn.recv(4).decode('utf-8')
            # Si no se recibe longitud, el cliente se ha desconectado
            if not msg_length:
                break
            
            msg_length = int(msg_length)
            
            message = conn.recv(msg_length).decode('utf-8')
            data = json.loads(message)
            
            action = data.get("action")
            secret_id = data.get("id")
            payload = data.get("payload")

            response = {"status": "error", "message": "Acción desconocida"}

            # Procesar solicitudes
            if action == "STORE": # Almacenar secreto
                if secret_id and payload:
                    vault_storage[secret_id] = payload
                    response = {"status": "success", "message": "Secreto almacenado (Cifrado)"}
                    print(f"[ALMACENAMIENTO] ID: {secret_id} guardado.")
                else:
                    response = {"status": "error", "message": "Faltan ID o Payload"}

            elif action == "RETRIEVE": # Recuperar secreto
                if secret_id in vault_storage:
                    response = {
                        "status": "success", 
                        "message": "Secreto recuperado", 
                        "payload": vault_storage[secret_id]
                    }
                    print(f"[RECUPERACIÓN] ID: {secret_id} enviado.")
                else:
                    response = {"status": "error", "message": "ID no encontrado"}

            elif action == "DISCONNECT":
                connected = False
                response = {"status": "success", "message": "Desconectando"}

            response_msg = json.dumps(response).encode('utf-8')
            msg_length = len(response_msg)
            
            # longitud (4 bytes) + mensaje
            conn.send(str(msg_length).encode('utf-8').ljust(4)) 
            conn.send(response_msg)

        except Exception as e:
            print(f"[ERROR] con {addr}: {e}")
            connected = False
    
    conn.close()
    print(f"[CONEXIÓN CERRADA] {addr} desconectado.")

def start_server():
    """Inicia el socket del servidor y acepta conexiones entrantes."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"[ESCUCHANDO] Servidor corriendo en {HOST}:{PORT}")
                
        while True:
            # Aceptar conexión
            conn, addr = server.accept()          
            handle_client(conn, addr)
            
    except KeyboardInterrupt:
        print("\n[APAGADO] Servidor deteniéndose...")
        server.close()
        sys.exit()

if __name__ == "__main__":
    start_server()