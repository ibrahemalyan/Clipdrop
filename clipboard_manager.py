import pyperclip
import os

class ClipboardManager:
    def __init__(self, history_file='history.txt'):
        self.clipboard_history = []
        self.history_file = history_file
        self.load_history_from_file()

    def add_clipboard_data(self, action, data):
        print(f"Added clipboard data: {action}, {data}")
        pyperclip.copy(data)
        self.clipboard_history.append((action, data))
        self.save_history_to_file()

    def load_history_from_file(self):
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as file:
                for line in file:
                    if ': ' in line:
                        action, data = line.strip().split(': ', 1)
                        self.clipboard_history.append((action, data))

    def save_history_to_file(self):
        with open(self.history_file, 'w') as file:
            for action, data in self.clipboard_history:
                if data=='':
                    continue
                file.write(f"{action}: {data}\n")

    def clear_history(self):
        self.clipboard_history = []
        self.save_history_to_file()
