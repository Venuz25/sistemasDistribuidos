import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox
from cryptography.fernet import Fernet
import base64

# Configuración del Cliente
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

class CryptoVaultClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Caja Fuerte Ciega")
        self.root.geometry("550x450")
        
        self.sock = None
        self.connected = False
        
        # --- Componentes de la UI ---
        self.create_widgets()
        
    def create_widgets(self):
        # Frame de Conexión
        conn_frame = ttk.LabelFrame(self.root, text="Conexión al Servidor")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(conn_frame, text="Conectar", command=self.connect_to_server).pack(side="left", padx=5, pady=5)
        self.lbl_status = ttk.Label(conn_frame, text="Estado: Desconectado", foreground="red")
        self.lbl_status.pack(side="left", padx=10)
        
        # Frame de Clave Criptográfica
        key_frame = ttk.LabelFrame(self.root, text="Clave Maestra (Cifrado Local)")
        key_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(key_frame, text="Clave Fernet (Base64):").pack(anchor="w", padx=5)
        self.entry_key = ttk.Entry(key_frame, width=65)
        self.entry_key.pack(padx=5, pady=2)
        
        ttk.Button(key_frame, text="Generar Nueva Clave", command=self.generate_key).pack(pady=2)
        ttk.Label(key_frame, text="*Esta clave nunca se envía al servidor", foreground="gray", font=("Arial", 8)).pack(anchor="w", padx=5)

        # Frame de Operaciones
        op_frame = ttk.LabelFrame(self.root, text="Operaciones de Almacenamiento")
        op_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        ttk.Label(op_frame, text="ID del Secreto (Único):").pack(anchor="w", padx=5)
        self.entry_id = ttk.Entry(op_frame)
        self.entry_id.pack(fill="x", padx=5, pady=2)
        
        ttk.Label(op_frame, text="Contenido (Texto Plano):").pack(anchor="w", padx=5)
        self.entry_content = ttk.Entry(op_frame)
        self.entry_content.pack(fill="x", padx=5, pady=2)
        
        btn_frame = ttk.Frame(op_frame)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Button(btn_frame, text="Guardar (Cifrar y Enviar)", command=lambda: self.thread_action(self.store_secret)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Recuperar (Recibir y Descifrar)", command=lambda: self.thread_action(self.retrieve_secret)).pack(side="left", padx=5)
        
        self.lbl_result = ttk.Label(op_frame, text="Resultado: ", wraplength=500, foreground="blue", justify="left")
        self.lbl_result.pack(padx=5, pady=5, anchor="w")

    def generate_key(self):
        """Genera una clave Fernet válida y la muestra en el campo."""
        key = Fernet.generate_key()
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, key.decode('utf-8'))
        messagebox.showinfo("Clave Generada", "Guarda esta clave en un lugar seguro. Sin ella no podrás recuperar tus datos.")

    def connect_to_server(self):
        """Establece la conexión TCP con el servidor."""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_HOST, SERVER_PORT))
            self.connected = True
            self.lbl_status.config(text="Estado: Conectado", foreground="green")
            self.lbl_result.config(text="Conexión exitosa. Listo para operar.", foreground="green")
        except Exception as e:
            messagebox.showerror("Error de Conexión", str(e))
            self.connected = False
            self.lbl_status.config(text="Estado: Error", foreground="red")

    def send_request(self, data_dict):
        """Envía datos al servidor siguiendo el protocolo de longitud prefijada."""
        if not self.connected or not self.sock:
            raise Exception("No hay conexión con el servidor")
        
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
        """Lógica Criptográfica de Almacenamiento."""
        try:
            key = self.entry_key.get().encode('utf-8')
            if not key:
                raise ValueError("Se requiere una clave maestra")
                
            f = Fernet(key)
            
            content = self.entry_content.get().encode('utf-8')
            secret_id = self.entry_id.get()
            
            if not content or not secret_id:
                raise ValueError("ID y Contenido son obligatorios")
            
            encrypted_token = f.encrypt(content)
            payload_b64 = base64.b64encode(encrypted_token).decode('utf-8')
            
            # Envío al servidor
            response = self.send_request({
                "action": "STORE",
                "id": secret_id,
                "payload": payload_b64
            })
            
            self.lbl_result.config(text=f"Servidor dice: {response['message']}", foreground="green")
            if response['status'] == 'success':
                self.entry_content.delete(0, tk.END)
                
        except Exception as e:
            self.lbl_result.config(text=f"Error: {str(e)}", foreground="red")

    def retrieve_secret(self):
        """Lógica Criptográfica de Recuperación."""
        try:
            key = self.entry_key.get().encode('utf-8')
            if not key:
                raise ValueError("Se requiere una clave maestra")
                
            f = Fernet(key)
            
            secret_id = self.entry_id.get()
            if not secret_id:
                raise ValueError("ID es obligatorio")
            
            # Solicitud al servidor
            response = self.send_request({
                "action": "RETRIEVE",
                "id": secret_id
            })
            
            if response['status'] == 'success':
                # Decodificar y Descifrar
                payload_b64 = response['payload']
                encrypted_token = base64.b64decode(payload_b64)
                decrypted_content = f.decrypt(encrypted_token).decode('utf-8')
                
                self.lbl_result.config(text=f"Secreto Recuperado: {decrypted_content}", foreground="green")
            else:
                self.lbl_result.config(text=f"Error: {response['message']}", foreground="red")
                
        except Exception as e:
            self.lbl_result.config(text=f"Error (Clave incorrecta o red): {str(e)}", foreground="red")

    def thread_action(self, target_func):
        if not self.connected:
            messagebox.showwarning("Atención", "Debes conectarte al servidor primero.")
            return
        
        thread = threading.Thread(target=target_func)
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = CryptoVaultClient(root)
    root.mainloop()