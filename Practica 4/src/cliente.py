"""
cliente.py - Cliente con Replicación Multi-Servidor
STORE: Guarda en TODOS los servidores
RETRIEVE: Recupera de CUALQUIER servidor disponible
"""

import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from cryptography.fernet import Fernet, InvalidToken
import base64
import time

# === CONFIGURACIÓN DE SERVIDORES DISPONIBLES ===
AVAILABLE_SERVERS = [
    ('127.0.0.1', 65432),  # Servidor 1
    ('127.0.0.1', 65433),  # Servidor 2
    ('127.0.0.1', 65434)   # Servidor 3
]

class CryptoVaultClient:
    """Cliente con conexión multi-servidor y replicación de datos"""
    
    def __init__(self, root):
        self.root = root
        self.sockets = {}  # {address: socket} - Múltiples conexiones
        self.server_info = {}  # {server_id: info}
        self.connected = False
        self.operation_lock = threading.Lock()
        self.socket_lock = threading.Lock()
        self.client_stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'replication_factor': 0
        }
        self.stats_lock = threading.Lock()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crea la interfaz gráfica con pestañas"""
        self.root.title("🔐 Caja Fuerte Ciega - Multi-Servidor con Replicación")
        self.root.geometry("900x750")
        
        # Notebook para pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña 0: Conexión y Estado
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text='🌐 Conexión y Estado')
        
        # Pestaña 1: Operaciones
        self.operations_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.operations_frame, text='📦 Operaciones')
        
        # Pestaña 2: Logs
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text='📋 Registro de Operaciones')
        
        # Pestaña 3: Estadísticas
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='📊 Estadísticas')
        
        self.create_connection_tab()
        self.create_operations_tab()
        self.create_log_tab()
        self.create_stats_tab()
        
        # Auto-conectar al iniciar
        self.root.after(1000, self.auto_connect_to_all_servers)
    
    def create_connection_tab(self):
        """Pestaña de conexión y estado de servidores"""
        # Panel de selección de servidor
        select_frame = ttk.LabelFrame(self.connection_frame, text="🔗 Servidores Disponibles")
        select_frame.pack(fill="x", padx=10, pady=10)
        
        # Lista de servidores
        self.servers_listbox = tk.Listbox(select_frame, height=4, font=("Consolas", 10))
        self.servers_listbox.pack(fill="x", padx=10, pady=5)
        
        for i, (host, port) in enumerate(AVAILABLE_SERVERS, 1):
            self.servers_listbox.insert(tk.END, f"Servidor {i} - {host}:{port}")
        
        # Botones de conexión
        btn_frame = ttk.Frame(select_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="🔗 Conectar a Todos", 
                   command=self.connect_to_all_servers,
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Desconectar Todos", 
                   command=self.disconnect_all,
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Verificar Estado", 
                   command=self.check_all_servers_status,
                   width=20).pack(side="left", padx=5)
        
        # Estado de conexión
        status_frame = ttk.LabelFrame(self.connection_frame, text="📡 Estado de Conexión")
        status_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_connection_status = ttk.Label(status_frame, 
            text="Estado: Desconectado", 
            foreground="red", 
            font=("Arial", 11, "bold"))
        self.lbl_connection_status.pack(padx=10, pady=5, anchor='w')
        
        self.lbl_replication_info = ttk.Label(status_frame, 
            text="", 
            foreground="blue",
            font=("Arial", 9))
        self.lbl_replication_info.pack(padx=10, pady=2, anchor='w')
        
        # Barra de progreso
        self.server_progress = ttk.Progressbar(status_frame, 
            orient='horizontal', 
            length=500, 
            mode='determinate')
        self.server_progress.pack(padx=10, pady=5)
        
        # Tabla de estado de servidores
        info_frame = ttk.LabelFrame(self.connection_frame, text="🖥️ Estado de Cada Servidor")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ('server_id', 'address', 'status', 'latency', 'secrets')
        self.server_tree = ttk.Treeview(info_frame, columns=columns, show='headings', height=6)
        
        self.server_tree.heading('server_id', text='ID Servidor')
        self.server_tree.heading('address', text='Dirección')
        self.server_tree.heading('status', text='Estado')
        self.server_tree.heading('latency', text='Latencia (ms)')
        self.server_tree.heading('secrets', text='Secretos')
        
        self.server_tree.column('server_id', width=100)
        self.server_tree.column('address', width=150)
        self.server_tree.column('status', width=100)
        self.server_tree.column('latency', width=100)
        self.server_tree.column('secrets', width=100)
        
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.server_tree.yview)
        self.server_tree.configure(yscrollcommand=scrollbar.set)
        
        self.server_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        self.server_tree.tag_configure('connected', foreground='green')
        self.server_tree.tag_configure('disconnected', foreground='red')
        
        # Instrucciones
        instructions = ttk.LabelFrame(self.connection_frame, text="ℹ️ Información de Replicación")
        instructions.pack(fill="x", padx=10, pady=10)
        
        instructions_text = """
        ✅ STORE: Los datos se guardan en TODOS los servidores disponibles (Replicación)
        ✅ RETRIEVE: Los datos se recuperan del PRIMER servidor que responda
        ✅ Si un servidor falla, los datos siguen disponibles en los demás
        ✅ Puedes conectarte/desconectarte de servidores individualmente
        """
        
        ttk.Label(instructions, text=instructions_text, 
                  justify="left", 
                  font=("Arial", 9),
                  foreground="green").pack(padx=10, pady=10, anchor="w")
    
    def create_operations_tab(self):
        """Pestaña de operaciones criptográficas"""
        # Panel de clave maestra
        crypto_frame = ttk.LabelFrame(self.operations_frame, text="🔑 Clave Maestra (Cifrado Local Zero-Knowledge)")
        crypto_frame.pack(fill="x", padx=10, pady=10)
        
        key_frame = ttk.Frame(crypto_frame)
        key_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(key_frame, text="Clave Fernet (Base64):", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        
        self.entry_key = ttk.Entry(key_frame, width=70, show='*')
        self.entry_key.pack(fill="x", padx=5, pady=2)
        
        btn_crypto_frame = ttk.Frame(key_frame)
        btn_crypto_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_crypto_frame, text="🎲 Generar Nueva", 
                   command=self.generate_key).pack(side="left", padx=2)
        ttk.Button(btn_crypto_frame, text="📋 Copiar", 
                   command=self.copy_key).pack(side="left", padx=2)
        ttk.Button(btn_crypto_frame, text="📥 Pegar", 
                   command=self.paste_key).pack(side="left", padx=2)
        ttk.Button(btn_crypto_frame, text="👁️ Mostrar/Ocultar", 
                   command=self.toggle_key_visibility).pack(side="left", padx=2)
        
        security_label = ttk.Label(key_frame, 
            text="⚠️ Esta clave NUNCA se envía al servidor. Guárdala en un lugar seguro.", 
            foreground="orange", 
            font=("Arial", 8, "italic"))
        security_label.pack(anchor="w", padx=5, pady=5)
        
        self.lbl_key_status = ttk.Label(key_frame, text="", foreground="gray")
        self.lbl_key_status.pack(anchor="w", padx=5, pady=2)
        
        # Panel de operaciones
        op_frame = ttk.LabelFrame(self.operations_frame, text="📝 Operaciones de Almacenamiento")
        op_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ID del Secreto
        id_frame = ttk.Frame(op_frame)
        id_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(id_frame, text="ID del Secreto:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        self.entry_id = ttk.Entry(id_frame, font=("Arial", 10))
        self.entry_id.pack(fill="x", padx=5, pady=2)
        
        # Contenido
        content_frame = ttk.Frame(op_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Label(content_frame, text="Contenido (Texto Plano):", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        self.entry_content = scrolledtext.ScrolledText(content_frame, height=6, font=("Arial", 10))
        self.entry_content.pack(fill="both", expand=True, padx=5, pady=2)
        
        # Botones de operación
        btn_frame = ttk.Frame(op_frame)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Button(btn_frame, text="💾 Guardar (Replicar)", 
                   command=self.store_secret,
                   width=18).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📥 Recuperar (Cualquier Servidor)", 
                   command=self.retrieve_secret,
                   width=25).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Listar IDs", 
                   command=self.list_ids,
                   width=15).pack(side="left", padx=2)
        
        # Resultado de operación
        result_frame = ttk.LabelFrame(op_frame, text="Resultado")
        result_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_result = ttk.Label(result_frame, 
            text="Esperando operación...", 
            wraplength=700, 
            foreground="blue",
            font=("Arial", 10))
        self.lbl_result.pack(padx=10, pady=10)
        
        self.lbl_replication = ttk.Label(result_frame, 
            text="", 
            wraplength=700, 
            foreground="gray",
            font=("Arial", 9))
        self.lbl_replication.pack(padx=10, pady=5)
    
    def create_log_tab(self):
        """Pestaña de registro de operaciones"""
        filter_frame = ttk.Frame(self.log_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(filter_frame, text="Filtrar por:").pack(side="left", padx=5)
        
        self.log_filter_var = tk.StringVar(value="TODOS")
        filter_combo = ttk.Combobox(filter_frame, 
            textvariable=self.log_filter_var,
            values=["TODOS", "STORE", "RETRIEVE", "LIST", "SUCCESS", "FAILED"],
            width=15)
        filter_combo.pack(side="left", padx=5)
        
        ttk.Button(filter_frame, text="🔄 Actualizar", 
                   command=self.get_log).pack(side="right", padx=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=25, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('FAILED', foreground='red')
        self.log_text.tag_config('STORE', foreground='blue')
        self.log_text.tag_config('RETRIEVE', foreground='purple')
        self.log_text.tag_config('INFO', foreground='gray')
    
    def create_stats_tab(self):
        """Pestaña de estadísticas"""
        self.server_stats_text = scrolledtext.ScrolledText(self.stats_frame, 
            height=20, 
            font=("Consolas", 10))
        self.server_stats_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        stats_btn_frame = ttk.Frame(self.stats_frame)
        stats_btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(stats_btn_frame, text="🔄 Actualizar Estadísticas", 
                   command=self.get_all_server_stats).pack(side="left", padx=5)
    
    def parse_server_list(self):
        """Obtiene la lista de servidores configurados"""
        return AVAILABLE_SERVERS
    
    def auto_connect_to_all_servers(self):
        """Auto-conecta a todos los servidores disponibles al iniciar"""
        self.connect_to_all_servers()
    
    def connect_to_all_servers(self):
        """Conecta a TODOS los servidores de la lista"""
        servers = self.parse_server_list()
        connected_count = 0
        self.server_info = {}
        
        with self.socket_lock:
            # Cerrar conexiones anteriores
            for addr, sock in self.sockets.items():
                try:
                    sock.close()
                except:
                    pass
            self.sockets = {}
        
        for addr in servers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                start_time = time.time()
                sock.connect(addr)
                latency = round((time.time() - start_time) * 1000, 2)
                
                with self.socket_lock:
                    self.sockets[addr] = sock
                
                server_id = self.get_server_id(sock)
                secrets_count = self.get_secrets_count(sock)
                
                self.server_info[server_id] = {
                    'address': f"{addr[0]}:{addr[1]}",
                    'status': 'connected',
                    'latency': latency,
                    'secrets_count': secrets_count,
                    'socket': sock
                }
                
                connected_count += 1
                print(f"✅ Conectado a {addr} (Server {server_id}) - {latency}ms")
                
            except Exception as e:
                print(f"❌ Fallo conexión a {addr}: {e}")
                self.server_info[f"{addr[0]}:{addr[1]}"] = {
                    'address': f"{addr[0]}:{addr[1]}",
                    'status': 'disconnected',
                    'latency': None,
                    'secrets_count': 0
                }
        
        self.connected = connected_count > 0
        
        with self.stats_lock:
            self.client_stats['replication_factor'] = connected_count
        
        # Actualizar UI
        self.update_connection_status(connected_count, len(servers))
        self.update_server_status_table(self.server_info)
        
        if connected_count > 0:
            self.lbl_result.config(
                text=f"✅ Conexión exitosa a {connected_count}/{len(servers)} servidores",
                foreground="green"
            )
            self.lbl_replication_info.config(
                text=f"📊 Factor de replicación: {connected_count} servidores",
                foreground="green"
            )
        else:
            self.lbl_result.config(
                text="❌ Error: No se pudo conectar a ningún servidor",
                foreground="red"
            )
    
    def get_server_id(self, sock):
        """Obtiene el ID del servidor"""
        try:
            self._send_raw(sock, {"action": "STATS"})
            length_msg = sock.recv(4).decode('utf-8')
            if length_msg:
                length = int(length_msg)
                response = json.loads(sock.recv(length).decode('utf-8'))
                return response.get('server_id', 'Unknown')
        except:
            pass
        return 'Unknown'
    
    def get_secrets_count(self, sock):
        """Obtiene la cantidad de secretos en el servidor"""
        try:
            self._send_raw(sock, {"action": "LIST"})
            length_msg = sock.recv(4).decode('utf-8')
            if length_msg:
                length = int(length_msg)
                response = json.loads(sock.recv(length).decode('utf-8'))
                return len(response.get('ids', []))
        except:
            pass
        return 0
    
    def disconnect_all(self):
        """Cierra todas las conexiones"""
        with self.socket_lock:
            for addr, sock in self.sockets.items():
                try:
                    self._send_raw(sock, {"action": "DISCONNECT"})
                    sock.close()
                except:
                    sock.close()
            self.sockets = {}
        
        self.server_info = {}
        self.connected = False
        
        self.update_connection_status(0, 0)
        self.update_server_status_table({})
        self.lbl_result.config(text="🔌 Desconectado de todos los servidores", foreground="gray")
        self.lbl_replication_info.config(text="")
    
    def _send_raw(self, sock, data_dict):
        """Envío crudo de datos a un socket específico"""
        msg = json.dumps(data_dict).encode('utf-8')
        msg_length = len(msg)
        sock.send(str(msg_length).encode('utf-8').ljust(4))
        sock.send(msg)
    
    def send_request_to_server(self, sock, data_dict):
        """Envía solicitud a un servidor específico y recibe respuesta"""
        with self.operation_lock:
            self._send_raw(sock, data_dict)
            
            length_msg = sock.recv(4).decode('utf-8')
            if not length_msg:
                raise Exception("Conexión cerrada por el servidor")
            
            length = int(length_msg)
            response = sock.recv(length).decode('utf-8')
            return json.loads(response)
    
    def store_secret(self):
        """
        ALMACENAMIENTO CON REPLICACIÓN
        Guarda en TODOS los servidores disponibles
        """
        try:
            key = self.entry_key.get().strip().encode('utf-8')
            if not key:
                raise ValueError("Se requiere clave maestra")
            
            try:
                f = Fernet(key)
            except:
                raise ValueError("Clave maestra inválida")
            
            content = self.entry_content.get('1.0', tk.END).strip().encode('utf-8')
            secret_id = self.entry_id.get().strip()
            
            if not content or not secret_id:
                raise ValueError("ID y Contenido obligatorios")
            
            # Cifrar localmente (Zero-Knowledge)
            encrypted_token = f.encrypt(content)
            payload_b64 = base64.b64encode(encrypted_token).decode('utf-8')
            
            # REPLICACIÓN: Enviar a TODOS los servidores
            success_count = 0
            failed_count = 0
            replication_details = []
            
            with self.socket_lock:
                servers_to_use = list(self.sockets.items())
            
            for addr, sock in servers_to_use:
                try:
                    response = self.send_request_to_server(sock, {
                        "action": "STORE",
                        "id": secret_id,
                        "payload": payload_b64,
                        "timestamp": time.time()
                    })
                    
                    if response.get('status') == 'success':
                        success_count += 1
                        server_id = response.get('server_id', 'Unknown')
                        replication_details.append(f"✅ Server {server_id}")
                    else:
                        failed_count += 1
                        replication_details.append(f"❌ Server {addr}")
                        
                except Exception as e:
                    failed_count += 1
                    replication_details.append(f"❌ {addr}: {str(e)[:30]}")
            
            with self.stats_lock:
                self.client_stats['total_operations'] += 1
                if success_count > 0:
                    self.client_stats['successful_operations'] += 1
                else:
                    self.client_stats['failed_operations'] += 1
            
            if success_count > 0:
                self.lbl_result.config(
                    text=f"✅ Guardado exitosamente en {success_count}/{len(servers_to_use)} servidores",
                    foreground="green"
                )
                self.lbl_replication.config(
                    text="Replicación: " + " | ".join(replication_details),
                    foreground="gray"
                )
                self.entry_content.delete('1.0', tk.END)
            else:
                self.lbl_result.config(
                    text="❌ Error: No se pudo guardar en ningún servidor",
                    foreground="red"
                )
                self.lbl_replication.config(
                    text="Fallos: " + " | ".join(replication_details),
                    foreground="gray"
                )
            
            self.check_all_servers_status()
            
        except Exception as e:
            self.lbl_result.config(text=f"❌ Error: {str(e)}", foreground="red")
    
    def retrieve_secret(self):
        """
        RECUPERACIÓN DESDE CUALQUIER SERVIDOR
        Intenta recuperar del PRIMER servidor que responda correctamente
        """
        try:
            key = self.entry_key.get().strip().encode('utf-8')
            if not key:
                raise ValueError("Se requiere clave maestra")
            
            try:
                f = Fernet(key)
            except:
                raise ValueError("Clave maestra inválida")
            
            secret_id = self.entry_id.get().strip()
            if not secret_id:
                raise ValueError("ID obligatorio")
            
            with self.socket_lock:
                servers_to_try = list(self.sockets.items())
            
            recovered_from = None
            decrypted_content = None
            
            # Intentar en cada servidor hasta encontrar el dato
            for addr, sock in servers_to_try:
                try:
                    response = self.send_request_to_server(sock, {
                        "action": "RETRIEVE",
                        "id": secret_id
                    })
                    
                    if response.get('status') == 'success':
                        payload_b64 = response.get('payload')
                        encrypted_token = base64.b64decode(payload_b64)
                        decrypted_content = f.decrypt(encrypted_token).decode('utf-8')
                        recovered_from = response.get('server_id', 'Unknown')
                        break  # Salir al encontrar el primero
                        
                except Exception as e:
                    print(f"Error recuperando de {addr}: {e}")
                    continue
            
            if decrypted_content:
                with self.stats_lock:
                    self.client_stats['total_operations'] += 1
                    self.client_stats['successful_operations'] += 1
                
                self.lbl_result.config(
                    text=f"✅ Secreto recuperado exitosamente",
                    foreground="green"
                )
                self.lbl_replication.config(
                    text=f"Recuperado de: Server {recovered_from} (los datos están replicados en todos los servidores)",
                    foreground="gray"
                )
                
                self.entry_content.delete('1.0', tk.END)
                self.entry_content.insert('1.0', decrypted_content)
            else:
                with self.stats_lock:
                    self.client_stats['total_operations'] += 1
                    self.client_stats['failed_operations'] += 1
                
                self.lbl_result.config(
                    text="❌ Error: No encontrado en ningún servidor",
                    foreground="red"
                )
                self.lbl_replication.config(
                    text=f"Se consultaron {len(servers_to_try)} servidores",
                    foreground="gray"
                )
            
        except InvalidToken:
            self.lbl_result.config(
                text="❌ Error: Clave incorrecta. No se puede descifrar el contenido.",
                foreground="red"
            )
        except Exception as e:
            self.lbl_result.config(text=f"❌ Error: {str(e)}", foreground="red")
    
    def list_ids(self):
        """Lista todos los IDs disponibles (del primer servidor que responda)"""
        try:
            with self.socket_lock:
                servers_to_try = list(self.sockets.items())
            
            for addr, sock in servers_to_try:
                try:
                    response = self.send_request_to_server(sock, {"action": "LIST"})
                    
                    if response.get('status') == 'success':
                        ids = response.get('ids', [])
                        server_id = response.get('server_id', 'Unknown')
                        
                        self.lbl_result.config(
                            text=f"✅ IDs disponibles: {len(ids)}",
                            foreground="green"
                        )
                        self.lbl_replication.config(
                            text=f"Fuente: Server {server_id} | IDs: {', '.join(ids[:10])}{'...' if len(ids) > 10 else ''}",
                            foreground="gray"
                        )
                        return
                        
                except:
                    continue
            
            self.lbl_result.config(text="❌ Error: No se pudo obtener lista de IDs", foreground="red")
            
        except Exception as e:
            self.lbl_result.config(text=f"❌ Error: {str(e)}", foreground="red")
    
    def get_log(self):
        """Obtiene el registro de operaciones de todos los servidores"""
        try:
            all_logs = []
            
            with self.socket_lock:
                servers_to_query = list(self.sockets.items())
            
            for addr, sock in servers_to_query:
                try:
                    response = self.send_request_to_server(sock, {"action": "LOG"})
                    
                    if response.get('status') == 'success':
                        logs = response.get('log', [])
                        all_logs.extend(logs)
                        
                except:
                    continue
            
            all_logs.sort(key=lambda x: x.get('timestamp', ''))
            self.update_log_display(all_logs)
            self.notebook.select(2)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener el log:\n{str(e)}")
    
    def get_all_server_stats(self):
        """Obtiene estadísticas de todos los servidores"""
        try:
            stats_text = "=== ESTADÍSTICAS DE SERVIDORES ===\n\n"
            
            with self.socket_lock:
                servers_to_query = list(self.sockets.items())
            
            for addr, sock in servers_to_query:
                try:
                    response = self.send_request_to_server(sock, {"action": "STATS"})
                    
                    if response.get('status') == 'success':
                        stats_text += f"Server {response.get('server_id', 'N/A')}:\n"
                        stats_text += f"  Uptime: {response.get('uptime', 'N/A')}\n"
                        stats_text += f"  Operaciones Totales: {response.get('total_operations', 0)}\n"
                        stats_text += f"  Exitosas: {response.get('successful_operations', 0)}\n"
                        stats_text += f"  Fallidas: {response.get('failed_operations', 0)}\n"
                        stats_text += f"  Conexiones Activas: {response.get('active_connections', 0)}\n\n"
                        
                except:
                    stats_text += f"Server {addr}: No disponible\n\n"
            
            with self.stats_lock:
                stats_text += "\n=== ESTADÍSTICAS DEL CLIENTE ===\n"
                stats_text += f"Operaciones Totales: {self.client_stats['total_operations']}\n"
                stats_text += f"Exitosas: {self.client_stats['successful_operations']}\n"
                stats_text += f"Fallidas: {self.client_stats['failed_operations']}\n"
                stats_text += f"Factor de Replicación: {self.client_stats['replication_factor']}\n"
            
            self.server_stats_text.delete('1.0', tk.END)
            self.server_stats_text.insert('1.0', stats_text)
            self.notebook.select(3)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo obtener estadísticas:\n{str(e)}")
    
    def check_all_servers_status(self):
        """Verifica el estado actual de todos los servidores"""
        for addr in list(self.sockets.keys()):
            try:
                sock = self.sockets[addr]
                start_time = time.time()
                response = self.send_request_to_server(sock, {"action": "STATS"})
                latency = round((time.time() - start_time) * 1000, 2)
                
                server_id = response.get('server_id', 'Unknown')
                secrets_count = self.get_secrets_count(sock)
                
                self.server_info[server_id] = {
                    'address': f"{addr[0]}:{addr[1]}",
                    'status': 'connected',
                    'latency': latency,
                    'secrets_count': secrets_count
                }
                
            except:
                for sid, info in self.server_info.items():
                    if info['address'] == f"{addr[0]}:{addr[1]}":
                        self.server_info[sid]['status'] = 'disconnected'
                        self.server_info[sid]['latency'] = None
        
        self.update_server_status_table(self.server_info)
    
    def update_connection_status(self, connected_count, total_servers):
        """Actualiza el estado de conexión en la UI"""
        if connected_count > 0:
            self.lbl_connection_status.config(
                text=f"Estado: ✅ Conectado ({connected_count}/{total_servers} servidores)", 
                foreground="green")
            self.server_progress['value'] = (connected_count / total_servers) * 100 if total_servers > 0 else 0
        else:
            self.lbl_connection_status.config(
                text="Estado: ❌ Desconectado", 
                foreground="red")
            self.server_progress['value'] = 0
    
    def update_server_status_table(self, servers_info):
        """Actualiza la tabla de estado de servidores"""
        for item in self.server_tree.get_children():
            self.server_tree.delete(item)
        
        for server_id, info in servers_info.items():
            status_tag = 'connected' if info['status'] == 'connected' else 'disconnected'
            self.server_tree.insert('', 'end', values=(
                f"Server {server_id}",
                info['address'],
                info['status'],
                f"{info['latency']}ms" if info['latency'] else "N/A",
                info['secrets_count']
            ), tags=(status_tag,))
    
    def update_log_display(self, log_entries):
        """Actualiza el display de logs con formato"""
        self.log_text.delete('1.0', tk.END)
        
        filter_type = self.log_filter_var.get()
        
        for entry in log_entries:
            if filter_type != "TODOS":
                if filter_type in ['SUCCESS', 'FAILED']:
                    if filter_type not in entry.get('status', ''):
                        continue
                elif filter_type != entry.get('operation', ''):
                    continue
            
            log_line = (f"[{entry.get('timestamp', 'N/A')}] "
                       f"Server {entry.get('server_id', 'N/A')} - "
                       f"{entry.get('operation', 'N/A')} "
                       f"(ID: {entry.get('id', 'N/A')}) - "
                       f"{entry.get('status', 'N/A')}\n")
            
            tag = entry.get('status', 'INFO')
            if 'SUCCESS' in tag:
                tag = 'SUCCESS'
            elif 'FAILED' in tag or 'ERROR' in tag:
                tag = 'FAILED'
            elif entry.get('operation') == 'STORE':
                tag = 'STORE'
            elif entry.get('operation') == 'RETRIEVE':
                tag = 'RETRIEVE'
            else:
                tag = 'INFO'
            
            self.log_text.insert(tk.END, log_line, tag)
        
        self.log_text.see(tk.END)
    
    def generate_key(self):
        """Genera nueva clave criptográfica"""
        key = Fernet.generate_key()
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, key.decode('utf-8'))
        self.validate_key()
        messagebox.showinfo("✅ Clave Generada", 
            "Guarda esta clave en un lugar seguro.\nSin ella no podrás recuperar tus secretos.")
    
    def copy_key(self):
        """Copia la clave al portapapeles"""
        key = self.entry_key.get()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("📋 Copiado", "Clave copiada al portapapeles")
    
    def paste_key(self):
        """Pega la clave del portapapeles"""
        try:
            key = self.root.clipboard_get()
            self.entry_key.delete(0, tk.END)
            self.entry_key.insert(0, key)
            self.validate_key()
        except:
            messagebox.showerror("❌ Error", "No hay clave en el portapapeles")
    
    def toggle_key_visibility(self):
        """Muestra/oculta la clave"""
        current_show = self.entry_key.cget('show')
        if current_show == '*':
            self.entry_key.config(show='')
        else:
            self.entry_key.config(show='*')
    
    def validate_key(self):
        """Valida el formato de la clave"""
        key = self.entry_key.get().strip()
        
        if not key:
            self.lbl_key_status.config(text="❌ Clave vacía", foreground="red")
            return False
        
        try:
            Fernet(key)
            self.lbl_key_status.config(text="✅ Clave válida", foreground="green")
            return True
        except:
            self.lbl_key_status.config(text="❌ Clave inválida", foreground="red")
            return False

def main():
    """Función principal de inicio"""
    root = tk.Tk()
    
    app = CryptoVaultClient(root)
    
    def on_closing():
        if app.connected:
            if messagebox.askokcancel("Salir", "¿Desconectar y salir?"):
                app.disconnect_all()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()