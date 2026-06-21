"""
ui.py - Interfaz Gráfica para Sistema Distribuido RMI (Pyro4)
Compatible con cliente_rmi.py (sin UI)
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from cryptography.fernet import Fernet

class CryptoVaultUI:
    """Clase principal de la interfaz gráfica"""
    
    def __init__(self, root, client_controller):
        self.root = root
        self.root.ui = self  # Referencia para que el cliente pueda actualizar UI
        self.client = client_controller
        self.ui_lock = threading.Lock()
        
        self.root.title("🔐 Caja Fuerte Ciega - Sistema Distribuido RMI")
        self.root.geometry("900x750")
        self.root.minsize(800, 650)
        
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
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connection_frame, text='🌐 Conexión y Estado')
        
        self.operations_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.operations_frame, text='📦 Operaciones')
        
        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text='📋 Registro de Operaciones')
        
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text='📊 Estadísticas')

    def create_connection_tab(self):
        select_frame = ttk.LabelFrame(self.connection_frame, text="🔗 Servidores Disponibles (RMI)")
        select_frame.pack(fill="x", padx=10, pady=10)
        
        self.servers_listbox = tk.Listbox(select_frame, height=4, font=("Consolas", 10))
        self.servers_listbox.pack(fill="x", padx=10, pady=5)
        
        self.available_servers = [
            "Servidor 1 - PYRO:vault.server1@127.0.0.1:9091",
            "Servidor 2 - PYRO:vault.server2@127.0.0.1:9092",
            "Servidor 3 - PYRO:vault.server3@127.0.0.1:9093"
        ]
        
        for server in self.available_servers:
            self.servers_listbox.insert(tk.END, server)
        
        btn_frame = ttk.Frame(select_frame)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="🔗 Conectar a Todos", 
                   command=lambda: self.safe_thread_action(self.client.connect_to_all_servers),
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ Desconectar Todos", 
                   command=lambda: self.safe_thread_action(self.client.disconnect_all),
                   width=20).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Verificar Estado", 
                   command=lambda: self.safe_thread_action(self.client.check_all_servers_status),
                   width=20).pack(side="left", padx=5)
        
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
        
        self.server_progress = ttk.Progressbar(status_frame, 
            orient='horizontal', 
            length=500, 
            mode='determinate')
        self.server_progress.pack(padx=10, pady=5)
        
        info_frame = ttk.LabelFrame(self.connection_frame, text="🖥️ Estado de Cada Servidor")
        info_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ('server_id', 'uri', 'status', 'latency')
        self.server_tree = ttk.Treeview(info_frame, columns=columns, show='headings', height=6)
        
        self.server_tree.heading('server_id', text='ID Servidor')
        self.server_tree.heading('uri', text='URI')
        self.server_tree.heading('status', text='Estado')
        self.server_tree.heading('latency', text='Latencia (ms)')
        
        self.server_tree.column('server_id', width=100)
        self.server_tree.column('uri', width=250)
        self.server_tree.column('status', width=100)
        self.server_tree.column('latency', width=100)
        
        scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.server_tree.yview)
        self.server_tree.configure(yscrollcommand=scrollbar.set)
        
        self.server_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        self.server_tree.tag_configure('connected', foreground='green')
        self.server_tree.tag_configure('disconnected', foreground='red')
        
        instructions = ttk.LabelFrame(self.connection_frame, text="ℹ️ Información de Replicación RMI")
        instructions.pack(fill="x", padx=10, pady=10)
        
        instructions_text = """
        ✅ STORE: Los datos se guardan en TODOS los servidores (Replicación)
        ✅ RETRIEVE: Los datos se recuperan del PRIMER servidor que responda
        ✅ Si un servidor falla, los datos siguen disponibles en los demás
        ✅ Comunicación vía RMI/Pyro4 (objetos distribuidos)
        """
        
        ttk.Label(instructions, text=instructions_text, 
                  justify="left", 
                  font=("Arial", 9),
                  foreground="green").pack(padx=10, pady=10, anchor="w")

    def create_operations_tab(self):
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
        
        self.lbl_key_status = ttk.Label(key_frame, text="", foreground="gray")
        self.lbl_key_status.pack(anchor="w", padx=5, pady=2)
        
        op_frame = ttk.LabelFrame(self.operations_frame, text="📝 Operaciones de Almacenamiento")
        op_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        id_frame = ttk.Frame(op_frame)
        id_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(id_frame, text="ID del Secreto:", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        self.entry_id = ttk.Entry(id_frame, font=("Arial", 10))
        self.entry_id.pack(fill="x", padx=5, pady=2)
        
        content_frame = ttk.Frame(op_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ttk.Label(content_frame, text="Contenido (Texto Plano):", font=("Arial", 9, "bold")).pack(anchor="w", padx=5, pady=2)
        self.entry_content = scrolledtext.ScrolledText(content_frame, height=6, font=("Arial", 10))
        self.entry_content.pack(fill="both", expand=True, padx=5, pady=2)
        
        btn_frame = ttk.Frame(op_frame)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        # === CORREGIDO: UI obtiene datos y llama al cliente ===
        ttk.Button(btn_frame, text="💾 Guardar (Replicar)", 
                   command=self._on_store_secret,
                   width=18).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📥 Recuperar", 
                   command=self._on_retrieve_secret,
                   width=25).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="📋 Listar IDs", 
                   command=lambda: self.safe_thread_action(self.client.list_ids),
                   width=15).pack(side="left", padx=2)
        
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
                   command=lambda: self.safe_thread_action(self.client.get_log)).pack(side="right", padx=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, height=25, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.log_text.tag_config('SUCCESS', foreground='green')
        self.log_text.tag_config('FAILED', foreground='red')
        self.log_text.tag_config('STORE', foreground='blue')
        self.log_text.tag_config('RETRIEVE', foreground='purple')
        self.log_text.tag_config('INFO', foreground='gray')

    def create_stats_tab(self):
        self.server_stats_text = scrolledtext.ScrolledText(self.stats_frame, 
            height=20, 
            font=("Consolas", 10))
        self.server_stats_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        stats_btn_frame = ttk.Frame(self.stats_frame)
        stats_btn_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(stats_btn_frame, text="🔄 Actualizar Estadísticas", 
                   command=lambda: self.safe_thread_action(self.client.get_all_server_stats)).pack(side="left", padx=5)

    def safe_thread_action(self, target_func):
        thread = threading.Thread(target=target_func, daemon=True)
        thread.start()

    def auto_connect_on_startup(self):
        if not self.client.connected:
            self.client.connect_to_all_servers()

    # === MÉTODOS AUXILIARES DE UI ===
    
    def _on_store_secret(self):
        """Obtiene datos de widgets y llama al cliente"""
        try:
            key = self.entry_key.get().strip().encode('utf-8')
            content = self.entry_content.get('1.0', tk.END).strip().encode('utf-8')
            secret_id = self.entry_id.get().strip()
            
            self.safe_thread_action(lambda: self.client.store_secret(key, content, secret_id))
        except Exception as e:
            self.update_result(f"❌ Error: {str(e)}", 'error')

    def _on_retrieve_secret(self):
        """Obtiene datos de widgets y llama al cliente"""
        try:
            key = self.entry_key.get().strip().encode('utf-8')
            secret_id = self.entry_id.get().strip()
            
            # Ejecutar en hilo y actualizar UI con el resultado
            def retrieve_and_update():
                result = self.client.retrieve_secret(key, secret_id)
                if result:
                    # Actualizar contenido en UI desde el hilo principal
                    self.root.after(0, lambda: self._update_content(result))
            
            self.safe_thread_action(retrieve_and_update)
        except Exception as e:
            self.update_result(f"❌ Error: {str(e)}", 'error')

    def _update_content(self, content):
        """Actualiza el contenido en el widget (debe llamarse desde hilo principal)"""
        self.entry_content.delete('1.0', tk.END)
        self.entry_content.insert('1.0', content)

    def generate_key(self):
        key = Fernet.generate_key()
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, key.decode('utf-8'))
        self.validate_key()
        messagebox.showinfo("✅ Clave Generada", 
             "Guarda esta clave en un lugar seguro.\nSin ella no podrás recuperar tus secretos.")

    def copy_key(self):
        key = self.entry_key.get()
        if key:
            self.root.clipboard_clear()
            self.root.clipboard_append(key)
            messagebox.showinfo("📋 Copiado", "Clave copiada al portapapeles")

    def paste_key(self):
        try:
            key = self.root.clipboard_get()
            self.entry_key.delete(0, tk.END)
            self.entry_key.insert(0, key)
            self.validate_key()
        except:
            messagebox.showerror("❌ Error", "No hay clave en el portapapeles")

    def toggle_key_visibility(self):
        current_show = self.entry_key.cget('show')
        if current_show == '*':
            self.entry_key.config(show='')
        else:
            self.entry_key.config(show='*')

    def validate_key(self):
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

    # === MÉTODOS DE ACTUALIZACIÓN DE UI ===
    
    def update_connection_status(self, connected_count, total_servers):
        with self.ui_lock:
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

    def update_replication_info(self, message):
        with self.ui_lock:
            self.lbl_replication_info.config(text=message)

    def update_server_info_table(self, servers_info):
        with self.ui_lock:
            for item in self.server_tree.get_children():
                self.server_tree.delete(item)
            
            for server_id, info in servers_info.items():
                status_tag = 'connected' if info['status'] == 'connected' else 'disconnected'
                self.server_tree.insert('', 'end', values=(
                    f"Server {server_id}",
                    info['uri'],
                    info['status'],
                    f"{info['latency']}ms" if info['latency'] else "N/A"
                ), tags=(status_tag,))

    def update_result(self, message, status='info'):
        with self.ui_lock:
            colors = {
                'success': 'green',
                'error': 'red',
                'warning': 'orange',
                'info': 'blue',
                'failover': 'orange'
            }
            self.lbl_result.config(text=message, foreground=colors.get(status, 'blue'))

    def update_replication_result(self, message):
        with self.ui_lock:
            self.lbl_replication.config(text=message)

    def update_log_display(self, log_entries):
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
                
                log_line = (f"[{entry.get('timestamp', 'N/A')}]  "
                           f"Server {entry.get('server_id', 'N/A')} -  "
                           f"{entry.get('operation', 'N/A')}  "
                           f"(ID: {entry.get('id', 'N/A')}) -  "
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

    def update_server_stats(self, stats_text):
        with self.ui_lock:
            self.server_stats_text.delete('1.0', tk.END)
            self.server_stats_text.insert('1.0', stats_text)


def main():
    """Función principal de inicio"""
    import cliente_rmi
    
    root = tk.Tk()
    client = cliente_rmi.CryptoVaultClient(root)
    app = CryptoVaultUI(root, client)
    
    def on_closing():
        if app.client.connected:
            if messagebox.askokcancel("Salir", "¿Desconectar y salir?"):
                app.client.disconnect_all()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()