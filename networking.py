import os
import socket
import threading
import time


class NetworkingManager:
    def __init__(self, host, port, broadcast_port, clients_update_callback):
        self.host = host
        self.port = port
        self.broadcast_port = broadcast_port
        self.clients_update_callback = clients_update_callback
        self.active_clients = {}
        self.pc_name = socket.gethostname()

    def broadcast_presence(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while True:
                try:
                    message = f"Presence: {self.pc_name}".encode('utf-8')
                    sock.sendto(message, ('<broadcast>', self.broadcast_port))
                    time.sleep(10)
                except Exception as e:
                    print(f"Error broadcasting presence: {e}")

    def listen_for_broadcasts(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('', self.broadcast_port))
            while True:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data:
                        client_name = data.decode('utf-8').split(": ")[1]
                        if client_name != self.pc_name:  # Skip if the client is the self PC
                            self.active_clients[addr[0]] = client_name
                            self.clients_update_callback()
                except Exception as e:
                    print(f"Error receiving broadcast: {e}")

    def handle_client_connection(self, client_socket, clipboard_manager):
        while True:
            try:
                data_type = client_socket.recv(1024).decode('utf-8')
                if data_type[:len("clipboard")] == 'clipboard':
                    clipboard_data = data_type[len("clipboard"):]
                    print(f"Received clipboard data: {clipboard_data}")
                    clipboard_manager.add_clipboard_data('received', clipboard_data)
                elif data_type == 'file':
                    file_name = client_socket.recv(1024).decode('utf-8')
                    file_size = int(client_socket.recv(1024).decode('utf-8'))
                    with open(file_name, 'wb') as f:
                        data = client_socket.recv(1024)
                        total_recv = len(data)
                        f.write(data)
                        while total_recv < file_size:
                            data = client_socket.recv(1024)
                            total_recv += len(data)
                            f.write(data)
                    print(f"Received file: {file_name}")
                else:
                    break
            except Exception as e:
                print(e)
                break
        client_socket.close()
    def refresh_clients_list(self):
        clients_to_remove = []
        for ip_address, client_name in self.active_clients.items():
            try:
                with socket.create_connection((ip_address, self.port), timeout=1):
                    pass
            except (socket.timeout, ConnectionRefusedError):
                clients_to_remove.append(ip_address)
        for ip_address in clients_to_remove:
            del self.active_clients[ip_address]
            print(f"Removed disconnected client: {ip_address}")
        self.clients_update_callback()

    def start_refreshing_clients_list(self):
        while True:
            self.refresh_clients_list()
            time.sleep(10)

    def start_server(self, clipboard_manager):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen(5)
        while True:
            client_sock, address = server.accept()
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_sock, clipboard_manager)
            )
            client_handler.start()
            refresh_thread = threading.Thread(target=self.start_refreshing_clients_list)
            refresh_thread.start()

    def send_clipboard_data(self, ip_address, clipboard_data):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Connecting to {ip_address}:{self.port}")
            client.connect((ip_address, self.port))
            print("Connected successfully")
            print(f"Sending clipboard data: {clipboard_data}")
            client.send(b'clipboard')
            client.send(clipboard_data.encode('utf-8'))
            print("Clipboard data sent successfully")
            client.close()
        except Exception as e:
            print(f"Error: {e}")

    def send_file(self, ip_address, file_path):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((ip_address, self.port))
            client.send(b'file')
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            client.send(file_name.encode('utf-8'))
            time.sleep(1)
            client.send(str(file_size).encode('utf-8'))
            time.sleep(1)
            with open(file_path, 'rb') as f:
                data = f.read(1024)
                while data:
                    client.send(data)
                    data = f.read(1024)
            client.close()
        except Exception as e:
            print(e)

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip
