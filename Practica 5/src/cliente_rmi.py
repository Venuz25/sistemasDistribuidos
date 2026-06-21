"""
cliente_rmi.py - Cliente con Objetos Distribuidos RMI
✅ Compatible con Pyro4 4.x y 5.x
✅ SIN UI - Solo lógica
"""
import Pyro4
import threading
from cryptography.fernet import Fernet, InvalidToken
import base64
import time

# === CONFIGURACIÓN DE SERVIDORES RMI ===
AVAILABLE_SERVERS = [
    ("vault.server1", "1"),
    ("vault.server2", "2"),
    ("vault.server3", "3"),
]

class CryptoVaultClient:
    """Cliente con conexión multi-servidor usando RMI/Pyro4 - SIN UI"""
    
    def __init__(self, root):
        self.root = root
        self.server_proxies = {}
        self.server_info = {}
        self.connected = False
        self.operation_lock = threading.Lock()
        self.client_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'replication_factor': 0
        }
        self.stats_lock = threading.Lock()
        
        # Configurar Pyro4
        Pyro4.config.SERIALIZER = 'json'
        Pyro4.config.COMMTIMEOUT = 5.0

    def connect_to_all_servers(self):
        """Conecta a TODOS los servidores RMI usando locateNS"""
        connected_count = 0
        self.server_proxies = {}
        self.server_info = {}
        
        for name, server_id in AVAILABLE_SERVERS:
            try:
                start_time = time.time()
                
                # ✅ locateNS funciona en Pyro4 4.x y 5.x
                ns = Pyro4.locateNS(host='127.0.0.1', port=9090)
                uri = ns.lookup(f"vault.server{server_id}")
                
                proxy = Pyro4.Proxy(uri)
                ping_result = proxy.ping()
                latency = round((time.time() - start_time) * 1000, 2)
                
                self.server_proxies[server_id] = proxy
                self.server_info[server_id] = {
                    'uri': str(uri),
                    'status': 'connected',
                    'latency': latency,
                    'server_id': ping_result.get('server_id', 'Unknown')
                }
                connected_count += 1
                print(f"✅ Conectado a Server {server_id} - {latency}ms")
                
            except Exception as e:
                print(f"❌ Fallo conexión a Server {server_id}: {e}")
                self.server_info[server_id] = {
                    'uri': f'PYRO:vault.server{server_id}@127.0.0.1:909{server_id}',
                    'status': 'disconnected',
                    'latency': None,
                    'server_id': 'Unknown'
                }
        
        self.connected = connected_count > 0
        
        with self.stats_lock:
            self.client_stats['replication_factor'] = connected_count
        
        # Actualizar UI (delegado a ui.py)
        self._ui_update('connection_status', connected_count, len(AVAILABLE_SERVERS))
        self._ui_update('server_info_table', self.server_info)
        
        if connected_count > 0:
            self._ui_update('replication_info', f"📊 Factor de replicación: {connected_count} servidores")
        else:
            self._ui_update('replication_info', "")

    def disconnect_all(self):
        """Cierra todas las conexiones RMI"""
        for server_id, proxy in self.server_proxies.items():
            try:
                proxy._pyroRelease()
            except:
                pass
        
        self.server_proxies = {}
        self.server_info = {}
        self.connected = False
        
        self._ui_update('connection_status', 0, 0)
        self._ui_update('server_info_table', {})
        self._ui_update('replication_info', "")

    def check_all_servers_status(self):
        """Verifica el estado actual de todos los servidores"""
        for server_id, proxy in list(self.server_proxies.items()):
            try:
                start_time = time.time()
                ping_result = proxy.ping()
                latency = round((time.time() - start_time) * 1000, 2)
                
                self.server_info[server_id]['status'] = 'connected'
                self.server_info[server_id]['latency'] = latency
                
            except:
                self.server_info[server_id]['status'] = 'disconnected'
                self.server_info[server_id]['latency'] = None
        
        self._ui_update('server_info_table', self.server_info)

    # === MÉTODOS DE OPERACIÓN - AHORA RECIBEN PARÁMETROS ===
    
    def store_secret(self, key, content, secret_id):
        """Almacena con replicación en todos los servidores
        
        Args:
            key: Clave Fernet (bytes)
            content: Contenido a cifrar (bytes)
            secret_id: ID del secreto (str)
        """
        try:
            if not key:
                raise ValueError("Se requiere clave maestra")
            
            f = Fernet(key)
            
            if not content or not secret_id:
                raise ValueError("ID y Contenido obligatorios")
            
            encrypted_token = f.encrypt(content)
            payload_b64 = base64.b64encode(encrypted_token).decode('utf-8')
            
            success_count = 0
            failed_count = 0
            replication_details = []
            
            for server_id, proxy in self.server_proxies.items():
                try:
                    response = proxy.store_secret(secret_id, payload_b64, time.time(), "RMI-Client")
                    
                    if response.get('status') == 'success':
                        success_count += 1
                        replication_details.append(f"✅ Server {server_id}")
                    else:
                        failed_count += 1
                        replication_details.append(f"❌ Server {server_id}")
                        
                except Exception as e:
                    failed_count += 1
                    replication_details.append(f"❌ Server {server_id}: {str(e)[:30]}")
            
            with self.stats_lock:
                self.client_stats['total_operations'] += 1
                if success_count > 0:
                    self.client_stats['successful_operations'] += 1
                else:
                    self.client_stats['failed_operations'] += 1
            
            if success_count > 0:
                self._ui_update('result', f"✅ Guardado en {success_count}/{len(self.server_proxies)} servidores", 'success')
                self._ui_update('replication_result', "Replicación: " + " | ".join(replication_details))
            else:
                self._ui_update('result', "❌ Error: No se pudo guardar", 'error')
                self._ui_update('replication_result', "Fallos: " + " | ".join(replication_details))
            
            self.check_all_servers_status()
            
        except Exception as e:
            self._ui_update('result', f"❌ Error: {str(e)}", 'error')

    def retrieve_secret(self, key, secret_id):
        """Recupera desde cualquier servidor
        
        Args:
            key: Clave Fernet (bytes)
            secret_id: ID del secreto (str)
            
        Returns:
            str: Contenido descifrado o None
        """
        try:
            if not key:
                raise ValueError("Se requiere clave maestra")
            
            f = Fernet(key)
            
            if not secret_id:
                raise ValueError("ID obligatorio")
            
            recovered_from = None
            decrypted_content = None
            
            for server_id, proxy in self.server_proxies.items():
                try:
                    response = proxy.retrieve_secret(secret_id, "RMI-Client")
                    
                    if response.get('status') == 'success':
                        payload_b64 = response.get('payload')
                        encrypted_token = base64.b64decode(payload_b64)
                        decrypted_content = f.decrypt(encrypted_token).decode('utf-8')
                        recovered_from = server_id
                        break
                        
                except Exception as e:
                    print(f"Error recuperando de Server {server_id}: {e}")
                    continue
            
            if decrypted_content:
                with self.stats_lock:
                    self.client_stats['total_operations'] += 1
                    self.client_stats['successful_operations'] += 1
                
                self._ui_update('result', "✅ Secreto recuperado", 'success')
                self._ui_update('replication_result', f"Recuperado de: Server {recovered_from}")
                return decrypted_content
            else:
                with self.stats_lock:
                    self.client_stats['total_operations'] += 1
                    self.client_stats['failed_operations'] += 1
                
                self._ui_update('result', "❌ No encontrado", 'error')
                self._ui_update('replication_result', f"Se consultaron {len(self.server_proxies)} servidores")
                return None
                
        except InvalidToken:
            self._ui_update('result', "❌ Clave incorrecta", 'error')
            return None
        except Exception as e:
            self._ui_update('result', f"❌ Error: {str(e)}", 'error')
            return None

    def list_ids(self):
        """Lista IDs disponibles"""
        try:
            for server_id, proxy in self.server_proxies.items():
                try:
                    response = proxy.list_ids("RMI-Client")
                    if response.get('status') == 'success':
                        ids = response.get('ids', [])
                        self._ui_update('result', f"✅ IDs disponibles: {len(ids)}", 'success')
                        self._ui_update('replication_result', f"Fuente: Server {server_id} | IDs: {', '.join(ids[:10])}")
                        return
                except:
                    continue
            
            self._ui_update('result', "❌ No se pudo obtener lista", 'error')
            
        except Exception as e:
            self._ui_update('result', f"❌ Error: {str(e)}", 'error')

    def get_log(self):
        """Obtiene logs de todos los servidores"""
        try:
            all_logs = []
            
            for server_id, proxy in self.server_proxies.items():
                try:
                    response = proxy.get_log("RMI-Client")
                    if response.get('status') == 'success':
                        logs = response.get('log', [])
                        all_logs.extend(logs)
                except:
                    continue
            
            all_logs.sort(key=lambda x: x.get('timestamp', ''))
            self._ui_update('log_display', all_logs)
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"No se pudo obtener el log:\n{str(e)}")

    def get_all_server_stats(self):
        """Obtiene estadísticas de todos los servidores"""
        try:
            stats_text = "=== ESTADÍSTICAS DE SERVIDORES (RMI) ===\n\n"
            
            for server_id, proxy in self.server_proxies.items():
                try:
                    response = proxy.get_stats("RMI-Client")
                    if response.get('status') == 'success':
                        stats_text += f"Server {server_id}:\n"
                        stats_text += f"  Uptime: {response.get('uptime', 'N/A')}\n"
                        stats_text += f"  Operaciones Totales: {response.get('total_operations', 0)}\n"
                        stats_text += f"  Exitosas: {response.get('successful_operations', 0)}\n"
                        stats_text += f"  Fallidas: {response.get('failed_operations', 0)}\n\n"
                except:
                    stats_text += f"Server {server_id}: No disponible\n\n"
            
            with self.stats_lock:
                stats_text += "\n=== ESTADÍSTICAS DEL CLIENTE ===\n"
                stats_text += f"Operaciones Totales: {self.client_stats['total_operations']}\n"
                stats_text += f"Exitosas: {self.client_stats['successful_operations']}\n"
                stats_text += f"Fallidas: {self.client_stats['failed_operations']}\n"
                stats_text += f"Factor de Replicación: {self.client_stats['replication_factor']}\n"
            
            self._ui_update('server_stats', stats_text)
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"No se pudo obtener estadísticas:\n{str(e)}")

    # === Métodos de actualización de UI (delegados a ui.py) ===
    def _ui_update(self, action, *args, **kwargs):
        """Delega actualizaciones de UI a ui.py"""
        if hasattr(self.root, 'ui'):
            ui = self.root.ui
            if action == 'connection_status':
                ui.update_connection_status(*args)
            elif action == 'server_info_table':
                ui.update_server_info_table(args[0])
            elif action == 'replication_info':
                ui.update_replication_info(args[0])
            elif action == 'result':
                ui.update_result(args[0], args[1] if len(args) > 1 else 'info')
            elif action == 'replication_result':
                ui.update_replication_result(args[0])
            elif action == 'log_display':
                ui.update_log_display(args[0])
            elif action == 'server_stats':
                ui.update_server_stats(args[0])