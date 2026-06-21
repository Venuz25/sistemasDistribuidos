"""
servidor.py - Nodo Servidor para Sistema Multi-Servidor
"""

import socket
import threading
import json
import sys
import time
import os
from datetime import datetime
from collections import deque

HOST = '0.0.0.0'
PORT = int(os.getenv('SERVER_PORT', 65432))
SERVER_ID = os.getenv('SERVER_ID', '1')
MAX_CONNECTIONS = 10

vault_storage = {}
storage_lock = threading.Lock()
connection_semaphore = threading.Semaphore(MAX_CONNECTIONS)
storage_condition = threading.Condition()
operation_log = deque(maxlen=100)
log_lock = threading.Lock()
active_connections = 0
connections_lock = threading.Lock()
server_stats = {
    'total_operations': 0,
    'successful_operations': 0,
    'failed_operations': 0,
    'start_time': time.time()
}
stats_lock = threading.Lock()

def log_operation(operation_type, secret_id, addr, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with log_lock:
        operation_log.append({
            "timestamp": timestamp,
            "operation": operation_type,
            "id": secret_id,
            "client": str(addr),
            "server_id": SERVER_ID,
            "status": status
        })
    
    with stats_lock:
        server_stats['total_operations'] += 1
        if status == 'SUCCESS':
            server_stats['successful_operations'] += 1
        else:
            server_stats['failed_operations'] += 1

def handle_client(conn, addr):
    global active_connections
    
    connection_semaphore.acquire()
    
    with connections_lock:
        active_connections += 1
        print(f"[SERVIDOR {SERVER_ID}] [NUEVA CONEXIÓN] {addr} conectado. Activas: {active_connections}/{MAX_CONNECTIONS}")
    
    connected = True
    
    try:
        while connected:
            try:
                msg_length = conn.recv(4).decode('utf-8')
                if not msg_length:
                    break
                msg_length = int(msg_length)
                
                message = conn.recv(msg_length).decode('utf-8')
                data = json.loads(message)
                
                action = data.get("action")
                secret_id = data.get("id")
                payload = data.get("payload")
                timestamp = data.get("timestamp", time.time())
                
                response = {"status": "error", "message": "Acción desconocida"}
                
                if action == "STORE":
                    with storage_lock:
                        if secret_id and payload:
                            is_update = secret_id in vault_storage
                            vault_storage[secret_id] = {
                                'payload': payload,
                                'timestamp': timestamp,
                                'server_id': SERVER_ID
                            }
                            
                            with storage_condition:
                                storage_condition.notify_all()
                            
                            response = {
                                "status": "success",
                                "message": "Secreto almacenado (Cifrado)",
                                "operation": "UPDATE" if is_update else "CREATE",
                                "server_id": SERVER_ID
                            }
                            log_operation("STORE", secret_id, addr, "SUCCESS")
                            print(f"[SERVIDOR {SERVER_ID}] [ALMACENAMIENTO] ID: {secret_id} por {addr}")
                        else:
                            response = {"status": "error", "message": "Faltan ID o Payload"}
                            log_operation("STORE", secret_id, addr, "FAILED")
                
                elif action == "RETRIEVE":
                    with storage_lock:
                        if secret_id in vault_storage:
                            response = {
                                "status": "success",
                                "message": "Secreto recuperado",
                                "payload": vault_storage[secret_id]['payload'],
                                "server_id": SERVER_ID
                            }
                            log_operation("RETRIEVE", secret_id, addr, "SUCCESS")
                            print(f"[SERVIDOR {SERVER_ID}] [RECUPERACIÓN] ID: {secret_id} enviado a {addr}")
                        else:
                            response = {"status": "error", "message": "ID no encontrado"}
                            log_operation("RETRIEVE", secret_id, addr, "FAILED")
                
                elif action == "LIST":
                    with storage_lock:
                        response = {
                            "status": "success",
                            "message": "Lista de IDs disponibles",
                            "ids": list(vault_storage.keys()),
                            "server_id": SERVER_ID
                        }
                        log_operation("LIST", "-", addr, "SUCCESS")
                
                elif action == "LOG":
                    with log_lock:
                        response = {
                            "status": "success",
                            "message": "Registro de operaciones",
                            "log": list(operation_log),
                            "server_id": SERVER_ID
                        }
                
                elif action == "STATS":
                    with stats_lock:
                        uptime = time.time() - server_stats['start_time']
                        response = {
                            "status": "success",
                            "message": "Estadísticas del servidor",
                            "server_id": SERVER_ID,
                            "uptime": f"{uptime:.2f} segundos",
                            "total_operations": server_stats['total_operations'],
                            "successful_operations": server_stats['successful_operations'],
                            "failed_operations": server_stats['failed_operations'],
                            "active_connections": active_connections
                        }
                
                elif action == "DISCONNECT":
                    connected = False
                    response = {"status": "success", "message": "Desconectando"}
                
                response_msg = json.dumps(response).encode('utf-8')
                msg_length = len(response_msg)
                conn.send(str(msg_length).encode('utf-8').ljust(4))
                conn.send(response_msg)
                
            except json.JSONDecodeError:
                print(f"[SERVIDOR {SERVER_ID}] [ERROR JSON] Datos inválidos de {addr}")
            except Exception as e:
                print(f"[SERVIDOR {SERVER_ID}] [ERROR] con {addr}: {e}")
                connected = False
    
    finally:
        conn.close()
        connection_semaphore.release()
        
        with connections_lock:
            active_connections -= 1
            print(f"[SERVIDOR {SERVER_ID}] [CONEXIÓN CERRADA] {addr}. Activas: {active_connections}/{MAX_CONNECTIONS}")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.settimeout(1.0)
    
    try:
        server.bind((HOST, PORT))
        server.listen(MAX_CONNECTIONS)
        print(f"\n{'='*60}")
        print(f"[SERVIDOR {SERVER_ID}] ESCUCHANDO en {HOST}:{PORT}")
        print(f"[CONFIG] Máximo {MAX_CONNECTIONS} conexiones concurrentes")
        print(f"{'='*60}\n")
        
        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except socket.timeout:
                continue
            
    except KeyboardInterrupt:
        print(f"\n[SERVIDOR {SERVER_ID}] [APAGADO] Deteniéndose...")
        server.close()
        sys.exit()

if __name__ == "__main__":
    start_server()