"""
ui.py - Interfaz Gráfica con Pestaña de Conexión Dedicada
Failover reactivo: solo cuando la conexión falla durante una operación
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime

class CryptoVaultUI:
    """Clase principal de la interfaz gráfica"""
    
    def __init__(self, root, client_controller):
        self.root = root
        self.client = client_controller
        self.ui_lock = threading.Lock()
        
        self.root.title("🔐 Caja Fuerte Ciega - Sistema Multi-Servidor con Failover")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.create_main_layout()
        self.create_connection_tab()
        self.create_operations_tab()
        self.create_log_tab()
        self.create_stats_tab()
        
        # Auto-conectar al iniciar
        self.root.after(1000, self.auto_connect_on_startup)
    
    def create_main_layout(self):
        """Crea el layout principal con Notebook para pestañas"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Pestaña 0: Conexión y Estado de Servidores
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text='🌐 Conexión y Estado')
        
        # Pestaña 1: Operaciones Principales
        self.operations_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.operations_frame, text='📦 Operaciones')
        
        # Pestaña 2: Logs
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text='📋 Registro de Operaciones')
        
        # Pestaña 3: Estadísticas
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='📊 Estadísticas')
    
    def create_connection_tab(self):
        """Pestaña dedicada para gestión de conexión y estado de servidores"""
        
        # Panel de selección de servidor
        select_frame = ttk.LabelFrame(self.connection_frame, text="🔗 Selección de Servidor")
        select_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(select_frame, text="Seleccionar Servidor:", 
                  font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky='w')
        
        # === COMBOBOX PARA SELECCIONAR SERVIDOR ===
        self.server_combo = ttk.Combobox(select_frame, width=45, state="readonly")
        self.server_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Lista de servidores disponibles
        self.available_servers = [
            "Servidor 1 - 127.0.0.1:65432",
            "Servidor 2 - 127.0.0.1:65433",
            "Servidor 3 - 127.0.0.1:65434"
        ]
        self.server_combo['values'] = self.available_servers
        self.server_combo.current(0)
        
        # Botones de conexión
        btn_frame = ttk.Frame(select_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=10)
        
        ttk.Button(btn_frame, text="🔗 Conectar", 
                   command=lambda: self.safe_thread_action(self.client.connect_to_server),
                   width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Desconectar", 
                   command=lambda: self.safe_thread_action(self.client.disconnect),
                   width=15).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Verificar Estado", 
                   command=lambda: self.safe_thread_action(self.client.check_server_status),
                   width=15).pack(side="left", padx=5)
        
        # Estado de conexión
        status_frame = ttk.LabelFrame(self.connection_frame, text="📡 Estado de Conexión")
        status_frame.pack(fill="x", padx=10, pady=10)
        
        self.lbl_connection_status = ttk.Label(status_frame, 
            text="Estado: Desconectado", 
            foreground="red", 
            font=("Arial", 11, "bold"))
        self.lbl_connection_status.pack(padx=10, pady=5, anchor='w')
        
        self.lbl_server_info = ttk.Label(status_frame, 
            text="", 
            foreground="gray",
            font=("Arial", 9))
        self.lbl_server_info.pack(padx=10, pady=2, anchor='w')
        
        # Indicador de failover
        self.lbl_failover = ttk.Label(status_frame, 
            text="", 
            foreground="orange",
            font=("Arial", 9, "italic"))
        self.lbl_failover.pack(padx=10, pady=2, anchor='w')
        
        # Tabla de información detallada del servidor
        info_frame = ttk.LabelFrame(self.connection_frame, text="🖥️ Información del Servidor Conectado")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ('property', 'value')
        self.server_info_tree = ttk.Treeview(info_frame, columns=columns, show='headings', height=8)
        
        self.server_info_tree.heading('property', text='Propiedad')
        self.server_info_tree.heading('value', text='Valor')
        
        self.server_info_tree.column('property', width=250)
        self.server_info_tree.column('value', width=400)
        
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.server_info_tree.yview)
        self.server_info_tree.configure(yscrollcommand=scrollbar.set)
        
        self.server_info_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # Lista rápida de todos los servidores disponibles
        servers_list_frame = ttk.LabelFrame(self.connection_frame, text="📋 Servidores Disponibles")
        servers_list_frame.pack(fill="x", padx=10, pady=10)
        
        self.servers_listbox = tk.Listbox(servers_list_frame, height=4, font=("Consolas", 10))
        self.servers_listbox.pack(fill="x", padx=10, pady=5)
        
        for server in self.available_servers:
            self.servers_listbox.insert(tk.END, server)
        
        # Instrucciones
        instructions = ttk.LabelFrame(self.connection_frame, text="ℹ️ Instrucciones")
        instructions.pack(fill="x", padx=10, pady=10)
        
        instructions_text = """
        1. Seleccione un servidor del menú desplegable
        2. Presione "Conectar" para establecer conexión
        3. La información del servidor se mostrará en la tabla
        4. Si el servidor falla durante una operación, se conectará automáticamente a otro
        5. Puede cambiar de servidor manualmente en cualquier momento
        """
        
        ttk.Label(instructions, text=instructions_text, 
                  justify="left", 
                  font=("Arial", 9)).pack(padx=10, pady=10, anchor="w")
    
    def create_operations_tab(self):
        """Pestaña para operaciones criptográficas"""
        
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
        
        ttk.Button(btn_frame, text="💾 Guardar", 
                   command=lambda: self.safe_thread_action(self.client.store_secret),
                   width=15).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📥 Recuperar", 
                   command=lambda: self.safe_thread_action(self.client.retrieve_secret),
                   width=15).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Listar IDs", 
                   command=lambda: self.safe_thread_action(self.client.list_ids),
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
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_log_display())
        
        ttk.Button(filter_frame, text="🔄 Actualizar", 
                   command=lambda: self.safe_thread_action(self.client.get_log)).pack(side="right", padx=5)
        ttk.Button(filter_frame, text="📥 Exportar", 
                   command=self.export_log).pack(side="right", padx=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=25, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('FAILED', foreground='red')
        self.log_text.tag_config('STORE', foreground='blue')
        self.log_text.tag_config('RETRIEVE', foreground='purple')
        self.log_text.tag_config('INFO', foreground='gray')
        self.log_text.tag_config('FAILOVER', foreground='orange')
    
    def create_stats_tab(self):
        """Pestaña de estadísticas"""
        server_stats_frame = ttk.LabelFrame(self.stats_frame, text="📊 Estadísticas del Servidor")
        server_stats_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.server_stats_text = scrolledtext.ScrolledText(server_stats_frame, 
            height=15, 
            font=("Consolas", 10))
        self.server_stats_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        stats_btn_frame = ttk.Frame(self.stats_frame)
        stats_btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(stats_btn_frame, text="🔄 Actualizar Estadísticas", 
                   command=lambda: self.safe_thread_action(self.client.get_server_stats)).pack(side="left", padx=5)
        
        # Explicación de estadísticas
        info_frame = ttk.LabelFrame(self.stats_frame, text="ℹ️ ¿Qué significan las estadísticas?")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        stats_explanation = """
        📌 UPTIME: Tiempo que el servidor ha estado funcionando sin reiniciarse.
        📌 OPERACIONES TOTALES: Número total de solicitudes recibidas.
        📌 OPERACIONES EXITOSAS: Solicitudes completadas correctamente.
        📌 OPERACIONES FALLIDAS: Solicitudes que fallaron.
        📌 CONEXIONES ACTIVAS: Clientes conectados actualmente.
        📌 LATENCIA: Tiempo de respuesta en milisegundos (ms).
        📌 FAILOVERS: Número de veces que el cliente se reconectó automáticamente a otro servidor.
        """
        
        ttk.Label(info_frame, text=stats_explanation, 
                  justify="left", 
                  font=("Arial", 9)).pack(padx=10, pady=10, anchor="w")
    
    def safe_thread_action(self, target_func):
        """Ejecuta operaciones en hilo secundario con protección de UI"""
        thread = threading.Thread(target=target_func, daemon=True)
        thread.start()
    
    def auto_connect_on_startup(self):
        """Auto-conecta al primer servidor disponible al iniciar"""
        if not self.client.connected:
            self.client.auto_connect_to_first_available()
    
    def generate_key(self):
        """Genera nueva clave criptográfica"""
        from cryptography.fernet import Fernet
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
        from cryptography.fernet import Fernet
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
    
    def update_connection_status(self, connected, server_address, latency=None):
        """Actualiza el estado de conexión en la UI"""
        with self.ui_lock:
            if connected:
                latency_text = f" ({latency}ms)" if latency else ""
                self.lbl_connection_status.config(
                    text=f"Estado: ✅ Conectado{latency_text}", 
                    foreground="green")
                self.lbl_server_info.config(
                    text=f"Servidor: {server_address}",
                    foreground="green")
            else:
                self.lbl_connection_status.config(
                    text="Estado: ❌ Desconectado", 
                    foreground="red")
                self.lbl_server_info.config(text="")
    
    def update_failover_status(self, message):
        """Actualiza el indicador de failover"""
        with self.ui_lock:
            self.lbl_failover.config(text=message)
    
    def update_server_info_table(self, server_info):
        """Actualiza la tabla de información del servidor"""
        with self.ui_lock:
            for item in self.server_info_tree.get_children():
                self.server_info_tree.delete(item)
            
            for property_name, value in server_info.items():
                self.server_info_tree.insert('', 'end', values=(property_name, value))
    
    def update_result(self, message, status='info'):
        """Actualiza el label de resultado"""
        with self.ui_lock:
            colors = {
                'success': 'green',
                'error': 'red',
                'warning': 'orange',
                'info': 'blue',
                'failover': 'orange'
            }
            self.lbl_result.config(text=message, foreground=colors.get(status, 'blue'))
    
    def update_log_display(self, log_entries):
        """Actualiza el display de logs con formato"""
        with self.ui_lock:
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
                elif 'FAILOVER' in entry.get('status', ''):
                    tag = 'FAILOVER'
                else:
                    tag = 'INFO'
                
                self.log_text.insert(tk.END, log_line, tag)
            
            self.log_text.see(tk.END)
    
    def refresh_log_display(self):
        """Refresca el display de logs con el filtro actual"""
        pass
    
    def export_log(self):
        """Exporta los logs a archivo"""
        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                log_content = self.log_text.get('1.0', tk.END)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("✅ Exportado", f"Logs exportados a:\n{file_path}")
            except Exception as e:
                messagebox.showerror("❌ Error", f"No se pudo exportar:\n{str(e)}")
    
    def update_server_stats(self, stats_text):
        """Actualiza el panel de estadísticas"""
        with self.ui_lock:
            self.server_stats_text.delete('1.0', tk.END)
            self.server_stats_text.insert('1.0', stats_text)