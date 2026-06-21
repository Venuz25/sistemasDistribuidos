"""
nameserver_starter.py - Inicia el Nameserver Pyro4
"""
import subprocess
import sys

def start_nameserver():
    """Inicia el nameserver usando el módulo integrado (siempre funciona)"""
    print("="*60)
    print("INICIANDO NAMESERVER PYRO4")
    print("="*60)
    
    try:
        # Usar el módulo integrado que siempre funciona
        result = subprocess.run([
            sys.executable, "-m", "Pyro4.naming", 
            "-n", "127.0.0.1", 
            "-p", "9090"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("Nameserver detenido correctamente")
        else:
            print("Nameserver terminó con error")
            
    except KeyboardInterrupt:
        print("\nNameserver detenido por usuario")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_nameserver()