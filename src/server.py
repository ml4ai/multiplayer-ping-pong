import socket
import threading
from utils import Network

PORT = 5050

def handle_client(connection, address):
    print("[SERVER] connected to: ", address)
    client_network = Network(connection)

    while True:
        try:
            data = client_network.receive()

            if data == 'x':
                break

            print(data)
        except socket.error as err:
            print(err)
            break

    print("Connection lost: ", address)
    connection.close()

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    host = socket.gethostbyname(socket.gethostname())
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Reuse socket
    server.bind((host, PORT))
    server.listen()
    print(f"[NETWORK] ({host}, {PORT})")

    while True:
        client_conn, client_addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_conn, client_addr))
        client_thread.start()
