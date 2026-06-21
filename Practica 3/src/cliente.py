import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
import base64
import time

# Configuración del Cliente
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

class CryptoVaultClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Caja Fuerte Ciega - Multi-Cliente")
        self.root.geometry("550x500")
        
        self.sock = None
        self.connected = False
        self.operation_lock = threading.Lock()  # Lock local para operaciones del cliente
        
        self.create_widgets()
        
    def create_widgets(self):
        # Frame de Conexión
        conn_frame = ttk.LabelFrame(self.root, text="Conexión al Servidor")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(conn_frame, text="Conectar", command=self.connect_to_server).pack(side="left", padx=5, pady=5)
        ttk.Button(conn_frame, text="Desconectar", command=self.disconnect).pack(side="left", padx=5, pady=5)
        self.lbl_status = ttk.Label(conn_frame, text="Estado: Desconectado", foreground="red")
        self.lbl_status.pack(side="left", padx=10)
        
        # Frame de Clave Criptográfica
        key_frame = ttk.LabelFrame(self.root, text="Clave Maestra (Cifrado Local)")
        key_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(key_frame, text="Clave Fernet (Base64):").pack(anchor="w", padx=5)
        self.entry_key = ttk.Entry(key_frame, width=55)
        self.entry_key.pack(padx=5, pady=2)
        
        ttk.Button(key_frame, text="Generar Nueva Clave", command=self.generate_key).pack(pady=2)
        ttk.Label(key_frame, text="*Esta clave nunca se envía al servidor", foreground="gray", font=("Arial", 8)).pack(anchor="w", padx=5)

        # Frame de Operaciones
        op_frame = ttk.LabelFrame(self.root, text="Operaciones")
        op_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Label(op_frame, text="ID del Secreto:").pack(anchor="w", padx=5)
        self.entry_id = ttk.Entry(op_frame)
        self.entry_id.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(op_frame, text="Contenido (Texto Plano):").pack(anchor="w", padx=5)
        self.entry_content = ttk.Entry(op_frame)
        self.entry_content.pack(fill="x", padx=5, pady=2)
        
        btn_frame = ttk.Frame(op_frame)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Button(btn_frame, text="Guardar", command=lambda: self.thread_action(self.store_secret)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Recuperar", command=lambda: self.thread_action(self.retrieve_secret)).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Listar IDs", command=lambda: self.thread_action(self.list_ids)).pack(side="left", padx=2)
        
        self.lbl_result = ttk.Label(op_frame, text="Resultado: ", wraplength=480, foreground="blue")
        self.lbl_result.pack(padx=5, pady=5)
        
        # Frame de Información del Servidor
        info_frame = ttk.LabelFrame(self.root, text="Información")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(info_frame, text="Ver Registro de Operaciones", command=lambda: self.thread_action(self.get_log)).pack(pady=2)

    def generate_key(self):
        key = Fernet.generate_key()
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, key.decode('utf-8'))
        messagebox.showinfo("Clave Generada", "Guarda esta clave en un lugar seguro.")

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(10)  # Timeout para operaciones
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.connected = True
            self.lbl_status.config(text="Estado: Conectado", foreground="green")
            self.lbl_result.config(text="Conexión exitosa.", foreground="green")
        except Exception as e:
            messagebox.showerror("Error de Conexión", str(e))
            self.connected = False
            self.lbl_status.config(text="Estado: Error", foreground="red")

    def disconnect(self):
        if self.connected and self.sock:
            try:
                self.send_request({"action": "DISCONNECT"})
                self.sock.close()
            except:
                pass
            finally:
                self.connected = False
                self.sock = None
                self.lbl_status.config(text="Estado: Desconectado", foreground="red")
                self.lbl_result.config(text="Desconectado del servidor.", foreground="gray")

    def send_request(self, data_dict):
        """Envía datos con control de concurrencia local"""
        if not self.connected or not self.sock:
            raise Exception("No hay conexión con el servidor")
        
        with self.operation_lock:  # Evita operaciones simultáneas desde el mismo cliente
            msg = json.dumps(data_dict).encode('utf-8')
            msg_length = len(msg)
            self.sock.send(str(msg_length).encode('utf-8').ljust(4))
            self.sock.send(msg)
            
            length_msg = self.sock.recv(4).decode('utf-8')
            if not length_msg:
                raise Exception("Conexión cerrada por el servidor")
            length = int(length_msg)
            response = self.sock.recv(length).decode('utf-8')
            return json.loads(response)

    def store_secret(self):
        """Almacenamiento con validación y manejo de errores"""
        try:
            key = self.entry_key.get().encode('utf-8')
            if not key:
                raise ValueError("Se requiere clave maestra")
                
            f = Fernet(key)
            content = self.entry_content.get().encode('utf-8')
            secret_id = self.entry_id.get()
            
            if not content or not secret_id:
                raise ValueError("ID y Contenido obligatorios")
            
            encrypted_token = f.encrypt(content)
            payload_b64 = base64.b64encode(encrypted_token).decode('utf-8')
            
            response = self.send_request({
                "action": "STORE",
                "id": secret_id,
                "payload": payload_b64,
                "timestamp": time.time()
            })
            
            op_type = response.get("operation", "")
            self.lbl_result.config(
                text=f"{response['message']} {op_type}", 
                foreground="green"
            )
            
            if response['status'] == 'success':
                self.entry_content.delete(0, tk.END)
                
        except Exception as e:
            self.lbl_result.config(text=f"Error: {str(e)}", foreground="red")

    def retrieve_secret(self):
        """Recuperación con validación de clave"""
        try:
            key = self.entry_key.get().encode('utf-8')
            if not key:
                raise ValueError("Se requiere clave maestra")
                
            f = Fernet(key)
            secret_id = self.entry_id.get()
            
            if not secret_id:
                raise ValueError("ID obligatorio")
            
            response = self.send_request({
                "action": "RETRIEVE",
                "id": secret_id
            })
            
            if response['status'] == 'success':
                payload_b64 = response['payload']
                encrypted_token = base64.b64decode(payload_b64)
                decrypted_content = f.decrypt(encrypted_token).decode('utf-8')
                self.lbl_result.config(text=f"Secreto: {decrypted_content}", foreground="green")
            else:
                self.lbl_result.config(text=f"Error: {response['message']}", foreground="red")
                
        except Exception as e:
            self.lbl_result.config(text=f"Error: {str(e)}", foreground="red")

    def list_ids(self):
        """Lista todos los IDs disponibles en el servidor"""
        try:
            response = self.send_request({"action": "LIST"})
            if response['status'] == 'success':
                ids = response.get("ids", [])
                self.lbl_result.config(text=f"IDs disponibles ({len(ids)}): {', '.join(ids)}", foreground="blue")
            else:
                self.lbl_result.config(text=f"Error: {response['message']}", foreground="red")
        except Exception as e:
            self.lbl_result.config(text=f"Error: {str(e)}", foreground="red")

    def get_log(self):
        """Obtiene el registro de operaciones del servidor"""
        try:
            response = self.send_request({"action": "LOG"})
            if response['status'] == 'success':
                log = response.get("log", [])
                log_text = "\n".join([f"{op['timestamp']} - {op['operation']} ({op['id']}): {op['status']}" for op in log[-10:]])
                messagebox.showinfo("Registro de Operaciones", log_text)
            else:
                messagebox.showerror("Error", response['message'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def thread_action(self, target_func):
        """Ejecuta operaciones en hilo secundario"""
        if not self.connected:
            messagebox.showwarning("Atención", "Debe conectarse primero.")
            return
        
        thread = threading.Thread(target=target_func, daemon=True)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoVaultClient(root)
    root.mainloop()