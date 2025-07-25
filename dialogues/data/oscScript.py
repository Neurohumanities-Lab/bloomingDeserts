import argparse
import random
import time

from pythonosc import udp_client

IP = "10.22.4.121"  # Escribe el IP aquí
PORT = 10000  # Escribe el puerto aquí

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--ip", default=IP, help="The ip of the OSC server")
  parser.add_argument("--port", type=str, default=PORT, help="The port the OSC server is listening on")
  args = parser.parse_args()

  client = udp_client.SimpleUDPClient(args.ip, args.port)

def enviar(x):
   client.send_message("/example", x)
