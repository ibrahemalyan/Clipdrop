from tkinter import *
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
from networking import NetworkingManager
from config_manager import ConfigManager
from clipboard_manager import ClipboardManager
from file_transfer import FileTransferManager
from ttkthemes import ThemedTk
import webbrowser
import pyperclip
class ClipDropGUI:
    def __init__(self):
        self.networking_manager = NetworkingManager(
            host='0.0.0.0',
            port=12345,
            broadcast_port=12346,
            clients_update_callback=self.update_clients_view
        )
        self.config_manager = ConfigManager()
        self.clipboard_manager = ClipboardManager()
        self.file_transfer_manager = FileTransferManager(update_progress_callback=self.update_progress)

        self.root = ThemedTk(theme="arc")
        self.root.title("ClipDrop")
        self.root.geometry("320x350")
        self.root.resizable(False, False)  # Disable resizing

        self.create_widgets()

        threading.Thread(target=self.networking_manager.broadcast_presence, daemon=True).start()
        threading.Thread(target=self.networking_manager.listen_for_broadcasts, daemon=True).start()
        threading.Thread(target=self.networking_manager.start_server, args=(self.clipboard_manager,), daemon=True).start()

        self.clipboard_manager.load_history_from_file()

        self.root.mainloop()

    def create_widgets(self):
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#ccc")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=1, fill='both')

        self.tab_clients = ttk.Frame(self.notebook)
        self.tab_history = ttk.Frame(self.notebook)
        self.tab_settings = ttk.Frame(self.notebook)
        self.tab_about = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_clients, text='Clients')
        self.notebook.add(self.tab_history, text='History')
        self.notebook.add(self.tab_settings, text='Settings')
        self.notebook.add(self.tab_about, text='About the Developer')

        self.create_clients_tab()
        self.create_history_tab()
        self.create_settings_tab()
        self.create_about_tab()

    def create_clients_tab(self):
        ttk.Label(self.tab_clients, text="Active Clients:").grid(column=0, row=0, pady=5, sticky=W)
        self.clients_frame = ttk.Frame(self.tab_clients)
        self.clients_frame.grid(column=0, row=1, pady=5, sticky=(W, E))

        copy_button = ttk.Button(self.tab_clients, text="Copy Last Received", command=self.copy_last_received)
        copy_button.grid(column=0, row=2, pady=5, sticky=(W, E))

        self.progress = ttk.Progressbar(self.tab_clients, orient=HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(column=0, row=3, pady=10)

        ttk.Label(self.tab_clients, text=f"Your IP: {self.networking_manager.get_ip_address()}").grid(column=0, row=4, pady=5, sticky=W)

    def create_history_tab(self):
        self.history_frame = ttk.Frame(self.tab_history)
        self.history_frame.pack(pady=10, padx=10, fill=BOTH, expand=True)

        self.history_text = Text(self.history_frame, height=15, width=50)
        self.history_text.pack(pady=10, padx=10, fill=BOTH, expand=True)

        clear_button = ttk.Button(self.history_frame, text="Clear History", command=self.clear_history)
        clear_button.pack(pady=5)

        self.update_history_view()

    def create_settings_tab(self):
        set_pc_name_button = ttk.Button(self.tab_settings, text="Set PC Name", command=self.set_pc_name)
        set_pc_name_button.pack(pady=10, padx=10)

        ttk.Label(self.tab_settings, text="Settings:").pack(pady=10)

    def create_about_tab(self):
        developer_info = """
        Developer: Ibrahem Alyan
        LinkedIn: https://www.linkedin.com/in/ibrahem-alyan-44026919b/
        GitHub: https://github.com/ibrahemalyan
        ClipDrop - All Rights Reserved 2024
        """
        about_text = Text(self.tab_about, height=15, width=50, wrap=WORD)
        about_text.insert(INSERT, developer_info)
        about_text.config(state=DISABLED)
        about_text.pack(pady=10, padx=10, fill=BOTH, expand=True)

        # Links
        link_frame = ttk.Frame(self.tab_about)
        link_frame.pack(pady=10)

        linkedin_btn = ttk.Button(link_frame, text="LinkedIn", command=lambda: self.open_link("https://www.linkedin.com/in/ibrahem-alyan-44026919b/"))
        linkedin_btn.grid(row=0, column=0, padx=10)

        github_btn = ttk.Button(link_frame, text="GitHub", command=lambda: self.open_link("https://github.com/ibrahemalyan"))
        github_btn.grid(row=0, column=1, padx=10)

    def update_clients_view(self):
        for widget in self.clients_frame.winfo_children():
            widget.destroy()
        row = 0
        col = 0
        for ip, name in self.networking_manager.active_clients.items():
            btn_frame = Frame(self.clients_frame)
            btn_frame.grid(row=row, column=col, padx=10, pady=5)
            btn = Button(btn_frame, text="●", font=("Arial", 16),
                         command=lambda ip=ip: self.networking_manager.send_clipboard_data(ip, pyperclip.paste()))
            btn.pack(side=TOP)
            file_btn = Button(btn_frame, text="Send File", command=lambda ip=ip: self.select_file_to_send(ip))
            file_btn.pack(side=BOTTOM)
            lbl = Label(self.clients_frame, text=name, font=("Arial", 10))
            lbl.grid(row=row + 1, column=col, padx=10, pady=0)
            col += 1
            if col > 4:
                col = 0
                row += 2

    def set_pc_name(self):
        new_name = simpledialog.askstring("Set PC Name", "Enter new PC name:", initialvalue=self.config_manager.pc_name)
        if new_name:
            self.config_manager.set_pc_name(new_name)

    def show_history(self):
        self.notebook.select(self.tab_history)
        self.update_history_view()

    def clear_history(self):
        self.clipboard_manager.clear_history()
        self.update_history_view()
        messagebox.showinfo("History", "Clipboard history cleared.")

    def update_history_view(self):
        self.history_text.delete(1.0, END)
        for action, data in self.clipboard_manager.clipboard_history:
            self.history_text.insert(END, f"{action}: {data[:30]}...\n")

    def copy_last_received(self):
        for action, data in reversed(self.clipboard_manager.clipboard_history):
            if action == "Received":
                pyperclip.copy(data)
                messagebox.showinfo("Clipboard", "Last received item copied to clipboard.")
                break

    def select_file_to_send(self, ip_address):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.file_transfer_manager.send_file(ip_address, file_path)

    def update_progress(self, current, total):
        if total > 0:
            self.progress['value'] = (current / total) * 100
            self.root.update_idletasks()

    def open_link(self, url):
        webbrowser.open(url)

if __name__ == "__main__":
    ClipDropGUI()
