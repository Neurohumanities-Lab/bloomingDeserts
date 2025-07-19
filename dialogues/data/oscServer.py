from pythonosc import dispatcher, osc_server
from queue import Queue
from threading import Thread

# Cola para almacenar mensajes entrantes
osc_queue = Queue()

# Manejador del mensaje recibido
def prompt_handler(address, *args):
    if args:
        osc_queue.put(args[0])

# Iniciar servidor OSC
def start_osc_server(ip="0.0.0.0", port=10001):
    port = int(port)  # <-- conversión segura
    disp = dispatcher.Dispatcher()
    disp.map("/prompt", prompt_handler)
    server = osc_server.ThreadingOSCUDPServer((ip, port), disp)
    print(f"[OSC Server] Escuchando en {ip}:{port}")
    server.serve_forever()

# Inicia el servidor en segundo plano
osc_server_started = False
def launch_osc_server_background(ip="0.0.0.0", port=10001):
    port = int(port)  # <-- conversión segura
    thread = Thread(target=start_osc_server, args=(ip, port), daemon=True)
    thread.start()
    return True

# Verifica si hay mensajes
def has_osc_message():
    return not osc_queue.empty()

# Obtiene el siguiente mensaje (o None si está vacía)
def get_osc_message():
    if not osc_queue.empty():
        return osc_queue.get()
    return None

