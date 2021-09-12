import socket
import threading
from utils import ClientNetwork

PORT = 5050

def handle_client(connection, address):
    print("[SERVER] connected to: ", address)
    client_network = ClientNetwork(connection)
    client_network.send([1, 2, 3])

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostbyname(socket.gethostname())
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
    server.bind((host, PORT))
    server.listen()
    print(f"[NETWORK] ({host}, {PORT})")

    client_thread = threading.Thread(target=handle_client, args=server.accept())
    client_thread.start()