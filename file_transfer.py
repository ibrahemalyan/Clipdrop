import socket
import time
import os
from tkinter import messagebox

class FileTransferManager:
    def __init__(self, update_progress_callback=None):
        self.update_progress_callback = update_progress_callback

    def handle_client_connection(self, client_socket):
        while True:
            try:
                data_type = client_socket.recv(1024).decode('utf-8')
                if data_type == 'file':
                    file_name = client_socket.recv(1024).decode('utf-8')
                    file_size = int(client_socket.recv(1024).decode('utf-8'))
                    with open(file_name, 'wb') as f:
                        data = client_socket.recv(1024)
                        total_recv = len(data)
                        f.write(data)
                        self.update_progress(total_recv, file_size)
                        while total_recv < file_size:
                            data = client_socket.recv(1024)
                            total_recv += len(data)
                            f.write(data)
                            self.update_progress(total_recv, file_size)
                    messagebox.showinfo("File Transfer", f"Received file: {file_name}")
                else:
                    break
            except Exception as e:
                print(e)
                break
        client_socket.close()

    def send_file(self, ip_address, file_path):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((ip_address, 12345))  # Adjust port as needed
            client.send(b'file')
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            client.send(file_name.encode('utf-8'))
            time.sleep(1)
            client.send(str(file_size).encode('utf-8'))
            time.sleep(1)
            with open(file_path, 'rb') as f:
                total_sent = 0
                data = f.read(1024)
                while data:
                    client.send(data)
                    total_sent += len(data)
                    self.update_progress(total_sent, file_size)
                    data = f.read(1024)
            messagebox.showinfo("File Transfer", f"Sent file: {file_name}")
            client.close()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to {ip_address}")
            print(e)

    def update_progress(self, current, total):
        if self.update_progress_callback:
            self.update_progress_callback(current, total)
