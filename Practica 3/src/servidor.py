import socket
import threading
import json
import sys
import time
from datetime import datetime
from collections import deque

# Configuración del Servidor
HOST = '0.0.0.0'
PORT = 65432
MAX_CONNECTIONS = 10  # Límite de clientes concurrentes

# Almacenamiento compartido protegido
vault_storage = {}

# === MECANISMOS DE SINCRONIZACIÓN ===

# Lock para proteger el acceso al diccionario compartido
storage_lock = threading.Lock()

# Semaphore para limitar conexiones concurrentes
connection_semaphore = threading.Semaphore(MAX_CONNECTIONS)

# Condition para notificar cambios en el almacenamiento
storage_condition = threading.Condition()

# Cola para registrar operaciones (auditoría)
operation_log = deque(maxlen=100)
log_lock = threading.Lock()

# Contador de conexiones activas
active_connections = 0
connections_lock = threading.Lock()

def log_operation(operation_type, secret_id, addr, status):
    """Registra operaciones en la cola de auditoría con timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_lock:
        operation_log.append({
            "timestamp": timestamp,
            "operation": operation_type,
            "id": secret_id,
            "client": str(addr),
            "status": status
        })

def handle_client(conn, addr):
    """
    Maneja la comunicación con un cliente específico.
    Incluye sincronización para acceso concurrente seguro.
    """
    global active_connections
    
    # Adquirir semáforo de conexión
    connection_semaphore.acquire()
    
    with connections_lock:
        active_connections += 1
        print(f"[NUEVA CONEXIÓN] {addr} conectado. Activas: {active_connections}/{MAX_CONNECTIONS}")
    
    connected = True
    
    try:
        while connected:
            try:
                # Recibir longitud del mensaje
                msg_length = conn.recv(4).decode('utf-8')
                if not msg_length:
                    break
                msg_length = int(msg_length)
                
                # Recibir payload JSON
                message = conn.recv(msg_length).decode('utf-8')
                data = json.loads(message)
                
                action = data.get("action")
                secret_id = data.get("id")
                payload = data.get("payload")
                timestamp = data.get("timestamp", time.time())

                response = {"status": "error", "message": "Acción desconocida"}

                # === SECCIÓN CRÍTICA PROTEGIDA POR LOCK ===
                if action == "STORE":
                    with storage_lock:  # Lock adquirido
                        if secret_id and payload:
                            is_update = secret_id in vault_storage
                            vault_storage[secret_id] = payload
                            
                            # Notificar a otras threads que hay cambio
                            with storage_condition:
                                storage_condition.notify_all()
                            
                            response = {
                                "status": "success", 
                                "message": "Secreto almacenado (Cifrado)",
                                "operation": "UPDATE" if is_update else "CREATE"
                            }
                            log_operation("STORE", secret_id, addr, "SUCCESS")
                            print(f"[ALMACENAMIENTO] ID: {secret_id} por {addr} {'(Actualizado)' if is_update else '(Nuevo)'}")
                        else:
                            response = {"status": "error", "message": "Faltan ID o Payload"}
                            log_operation("STORE", secret_id, addr, "FAILED")

                elif action == "RETRIEVE":
                    with storage_lock:  # Lock adquirido
                        if secret_id in vault_storage:
                            response = {
                                "status": "success", 
                                "message": "Secreto recuperado", 
                                "payload": vault_storage[secret_id]
                            }
                            log_operation("RETRIEVE", secret_id, addr, "SUCCESS")
                            print(f"[RECUPERACIÓN] ID: {secret_id} enviado a {addr}")
                        else:
                            response = {"status": "error", "message": "ID no encontrado"}
                            log_operation("RETRIEVE", secret_id, addr, "FAILED")

                elif action == "LIST":
                    with storage_lock:
                        response = {
                            "status": "success",
                            "message": "Lista de IDs disponibles",
                            "ids": list(vault_storage.keys())
                        }
                        log_operation("LIST", "-", addr, "SUCCESS")

                elif action == "LOG":
                    with log_lock:
                        response = {
                            "status": "success",
                            "message": "Registro de operaciones",
                            "log": list(operation_log)
                        }

                elif action == "DISCONNECT":
                    connected = False
                    response = {"status": "success", "message": "Desconectando"}

                # Enviar respuesta
                response_msg = json.dumps(response).encode('utf-8')
                msg_length = len(response_msg)
                conn.send(str(msg_length).encode('utf-8').ljust(4))
                conn.send(response_msg)

            except json.JSONDecodeError:
                print(f"[ERROR JSON] Datos inválidos de {addr}")
                response = {"status": "error", "message": "Formato JSON inválido"}
            except Exception as e:
                print(f"[ERROR] con {addr}: {e}")
                connected = False
    
    finally:
        # Liberar recursos
        conn.close()
        connection_semaphore.release()
        
        with connections_lock:
            active_connections -= 1
            print(f"[CONEXIÓN CERRADA] {addr}. Activas: {active_connections}/{MAX_CONNECTIONS}")

def start_server():
    """Inicia el servidor con control de concurrencia"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(1.0)
    
    try:
        server.bind((HOST, PORT))
        server.listen(MAX_CONNECTIONS)
        print(f"[ESCUCHANDO] Servidor en {HOST}:{PORT}")
        print(f"[CONFIG] Máximo {MAX_CONNECTIONS} conexiones concurrentes")
        print(f"[CONFIG] Lock: {type(storage_lock).__name__}")
        print(f"[CONFIG] Semaphore: {connection_semaphore._value} disponibles")
        
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except socket.timeout:
                continue
            
    except KeyboardInterrupt:
        print("\n[APAGADO] Servidor deteniéndose...")
        print(f"[ESTADÍSTICAS] Operaciones registradas: {len(operation_log)}")
        server.close()
        sys.exit()

if __name__ == "__main__":
    start_server()