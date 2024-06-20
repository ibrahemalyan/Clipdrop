import configparser
import os
import socket


class ConfigManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.pc_name = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            self.config['SETTINGS'] = {'PC_NAME': socket.gethostname()}
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
        else:
            self.config.read(self.config_file)
        return self.config['SETTINGS']['PC_NAME']

    def set_pc_name(self, new_name):
        self.pc_name = new_name
        self.config['SETTINGS']['PC_NAME'] = new_name
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
