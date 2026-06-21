"""
servidor_rmi.py - Nodo Servidor como Objeto Distribuido RMI
✅ Compatible con Pyro4 4.x y 5.x
"""
import Pyro4
import threading
import time
import os
from datetime import datetime
from collections import deque

@Pyro4.expose
class VaultServer:
    """Objeto remoto que representa un servidor de vault"""
    
    def __init__(self, server_id, port):
        self.server_id = server_id
        self.port = port
        self.vault_storage = {}
        self.storage_lock = threading.Lock()
        self.operation_log = deque(maxlen=100)
        self.log_lock = threading.Lock()
        self.server_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'start_time': time.time()
        }
        self.stats_lock = threading.Lock()
        
    def _log_operation(self, operation_type, secret_id, client_addr, status):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.log_lock:
            self.operation_log.append({
                "timestamp": timestamp,
                "operation": operation_type,
                "id": secret_id,
                "client": str(client_addr),
                "server_id": self.server_id,
                "status": status
            })
        with self.stats_lock:
            self.server_stats['total_operations'] += 1
            if status == 'SUCCESS':
                self.server_stats['successful_operations'] += 1
            else:
                self.server_stats['failed_operations'] += 1
    
    def store_secret(self, secret_id, payload, timestamp=None, client_addr="unknown"):
        timestamp = timestamp or time.time()
        with self.storage_lock:
            if secret_id and payload:
                is_update = secret_id in self.vault_storage
                self.vault_storage[secret_id] = {
                    'payload': payload,
                    'timestamp': timestamp,
                    'server_id': self.server_id
                }
                self._log_operation("STORE", secret_id, client_addr, "SUCCESS")
                print(f"[SERVIDOR {self.server_id}] [ALMACENAMIENTO] ID: {secret_id}")
                return {
                    "status": "success",
                    "message": "Secreto almacenado (Cifrado)",
                    "operation": "UPDATE" if is_update else "CREATE",
                    "server_id": self.server_id
                }
            else:
                self._log_operation("STORE", secret_id, client_addr, "FAILED")
                return {"status": "error", "message": "Faltan ID o Payload"}
    
    def retrieve_secret(self, secret_id, client_addr="unknown"):
        with self.storage_lock:
            if secret_id in self.vault_storage:
                self._log_operation("RETRIEVE", secret_id, client_addr, "SUCCESS")
                print(f"[SERVIDOR {self.server_id}] [RECUPERACIÓN] ID: {secret_id}")
                return {
                    "status": "success",
                    "message": "Secreto recuperado",
                    "payload": self.vault_storage[secret_id]['payload'],
                    "server_id": self.server_id
                }
            else:
                self._log_operation("RETRIEVE", secret_id, client_addr, "FAILED")
                return {"status": "error", "message": "ID no encontrado"}
    
    def list_ids(self, client_addr="unknown"):
        with self.storage_lock:
            self._log_operation("LIST", "-", client_addr, "SUCCESS")
            return {
                "status": "success",
                "message": "Lista de IDs disponibles",
                "ids": list(self.vault_storage.keys()),
                "server_id": self.server_id
            }
    
    def get_log(self, client_addr="unknown"):
        with self.log_lock:
            return {
                "status": "success",
                "message": "Registro de operaciones",
                "log": list(self.operation_log),
                "server_id": self.server_id
            }
    
    def get_stats(self, client_addr="unknown"):
        with self.stats_lock:
            uptime = time.time() - self.server_stats['start_time']
            return {
                "status": "success",
                "message": "Estadísticas del servidor",
                "server_id": self.server_id,
                "uptime": f"{uptime:.2f} segundos",
                "total_operations": self.server_stats['total_operations'],
                "successful_operations": self.server_stats['successful_operations'],
                "failed_operations": self.server_stats['failed_operations']
            }
    
    def ping(self):
        return {"status": "success", "server_id": self.server_id, "timestamp": time.time()}


def start_server(server_id, port):
    """Inicia el servidor RMI - Compatible con Pyro4 4.x y 5.x"""
    Pyro4.config.SERIALIZER = 'json'
    
    vault_server = VaultServer(server_id, port)
    
    try:
        # Crear daemon en el puerto del servidor
        daemon = Pyro4.Daemon(host='127.0.0.1', port=port)
        
        # Conectar al nameserver (puerto 9090) - FUNCIONA EN AMBAS VERSIONES
        ns = Pyro4.locateNS(host='127.0.0.1', port=9090)
        
        # Registrar el objeto remoto
        uri = daemon.register(vault_server, f"vault.server{server_id}")
        ns.register(f"vault.server{server_id}", uri)
        
        print(f"\n{'='*60}")
        print(f"[SERVIDOR {server_id}] RMI ACTIVO en 127.0.0.1:{port}")
        print(f"[URI] {uri}")
        print(f"[REGISTRO] vault.server{server_id} en nameserver")
        print(f"{'='*60}\n")
        
        # Loop principal
        daemon.requestLoop()
        
    except Exception as e:
        print(f"[ERROR] No se pudo iniciar: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    server_id = os.getenv('SERVER_ID', '1')
    port = int(os.getenv('SERVER_PORT', '9091'))
    start_server(server_id, port)