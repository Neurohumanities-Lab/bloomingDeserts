from pythonosc import dispatcher
from pythonosc import osc_server
from threading import Thread
from queue import Queue
import socketserver

osc_queue = Queue()
server_instance = None

class ReusableOSCServer(osc_server.ThreadingOSCUDPServer):
    allow_reuse_address = True

def handle_osc_message(address, *args):
    message = " ".join(map(str, args))
    print(f"[OSC] Recibido en {address}: {message}")
    osc_queue.put(message)

osc_dispatcher = dispatcher.Dispatcher()
osc_dispatcher.map("/*", handle_osc_message)

def start_osc_server(ip="0.0.0.0", port=10001):
    global server_instance
    if server_instance is None:
        server_instance = ReusableOSCServer((ip, port), osc_dispatcher)
        print(f"[OSC Server] Escuchando en {ip}:{port}")
        server_instance.serve_forever()
    else:
        print("[OSC Server] Ya está corriendo")

def run_server_thread():
    thread = Thread(target=start_osc_server, daemon=True)
    thread.start()

def stop_osc_server():
    global server_instance
    if server_instance:
        print("[OSC Server] Deteniendo servidor...")
        server_instance.shutdown()
        server_instance.server_close()
        server_instance = None

def has_osc_message():
    return not osc_queue.empty()

def get_osc_message():
    if not osc_queue.empty():
        return osc_queue.get()
    return None
