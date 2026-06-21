import threading
import os
import multiprocessing
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageOps
import time

class AppProcesamiento:
    def __init__(self, root):
        self.root = root
        self.root.title("Práctica 1 - Multiprocesamiento")
        self.root.geometry("450x450")

        self.ruta_carpeta = tk.StringVar()
        self.progreso_var = tk.DoubleVar()
        self.modo_var = tk.StringVar(value="Paralelo")
        self.hilos_activos = []
        self.lock = threading.Lock()

        # --- Interfaz Gráfica ---
        tk.Label(root, text="Multiprocesamiento", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(root, text="Procesamiento de imágenes en lote", font=("Arial", 10)).pack()

        tk.Label(root, text="Seleccione modo de ejecución:", font=("Arial", 9, "italic")).pack(pady=5)
        self.combo_modo = ttk.Combobox(root, textvariable=self.modo_var, values=["Secuencial", "Paralelo"], state="readonly")
        self.combo_modo.pack()
        
        tk.Button(root, text="Seleccionar Carpeta", command=self.seleccionar_carpeta).pack(pady=15)
        tk.Label(root, textvariable=self.ruta_carpeta, fg="blue", wraplength=350).pack()

        self.btn_iniciar = tk.Button(root, text="Iniciar Proceso", state="disabled", command=self.gestionar_inicio, bg="#41984F", fg="white", font=("Arial", 10, "bold"))
        self.btn_iniciar.pack(pady=10)

        self.barra_progreso = ttk.Progressbar(root, variable=self.progreso_var, maximum=100, length=300)
        self.barra_progreso.pack(pady=10)

        self.lbl_estado = tk.Label(root, text="Estado: Sistema Listo")
        self.lbl_estado.pack()

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta_carpeta.set(carpeta)
            self.btn_iniciar.config(state="normal")

    def procesoImg (self, lista_fotos, carpeta_origen, carpeta_destino, nombre_hilo):
        """Procesamiento de imágenes"""
        print(f"[INICIO] {nombre_hilo} trabajando...")
        
        for foto in lista_fotos:
            ruta_in = os.path.join(carpeta_origen, foto)
            ruta_out = os.path.join(carpeta_destino, f"proc_{foto}")
            
            try:
                with Image.open(ruta_in) as img:
                    img_gris = ImageOps.grayscale(img)
                    img_gris.save(ruta_out)
                
                with self.lock:
                    actual = self.progreso_var.get()
                    self.root.after(0, self.progreso_var.set, actual + (100 / self.total_fotos))
                
                print(f"{nombre_hilo} proceso: {foto}")
                    
            except Exception as e:
                print(f"Error en {nombre_hilo} con {foto}: {e}")

        print(f"[FINAL] {nombre_hilo} termino.")

    def gestionar_inicio(self):
        """Prepara el entorno y decide si ir por secuencial o paralelo"""
        origen = self.ruta_carpeta.get()
        destino = os.path.join(origen, "imgProcesadas")
        archivos = [f for f in os.listdir(origen) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not archivos:
            messagebox.showwarning("Error", "No se encontraron imágenes.")
            return

        if not os.path.exists(destino): os.makedirs(destino)

        self.total_fotos = len(archivos)
        self.progreso_var.set(0)
        self.btn_iniciar.config(state="disabled")
        self.lbl_estado.config(text="Procesando...")
        self.tiempo_inicio = time.time()

        if self.modo_var.get() == "Secuencial":
            threading.Thread(target=self.ejecutar_secuencial, args=(archivos, origen, destino), daemon=True).start()
        else:
            self.lanzar_paralelo(archivos, origen, destino)

    def ejecutar_secuencial(self, archivos, origen, destino):
        print("\n--- Iniciando Modo Secuencial (1 Hilo) ---")
        self.procesoImg (archivos, origen, destino, "Hilo-Unico")
        self.root.after(0, self.notificar_termino)

    def lanzar_paralelo(self, archivos, origen, destino):
        self.hilos_activos = []
        num_hilos = multiprocessing.cpu_count() 
        paso = len(archivos) // num_hilos
        
        print(f"\n--- Iniciando Multiprocesamiento: {num_hilos} hilos ---")

        for i in range(num_hilos):
            inicio = i * paso
            fin = None if i == num_hilos - 1 else (i + 1) * paso
            lote = archivos[inicio:fin]
            
            t = threading.Thread(target=self.procesoImg , args=(lote, origen, destino, f"hiloTrabajador{i+1}"), daemon=True)
            self.hilos_activos.append(t)
            t.start()

        threading.Thread(target=self.monitor_finalizacion, daemon=True).start()

    def monitor_finalizacion(self):
        for t in self.hilos_activos:
            t.join()
        self.root.after(0, self.notificar_termino)

    def notificar_termino(self):
        tiempo_total = time.time() - self.tiempo_inicio
        self.btn_iniciar.config(state="normal")
        self.lbl_estado.config(text=f"Completado en {tiempo_total:.2f}s")
        messagebox.showinfo("Proceso Terminado", 
                            f"Modo: {self.modo_var.get()}\nTiempo: {tiempo_total:.2f} seg\nFotos: {self.total_fotos}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppProcesamiento(root)
    root.mainloop()