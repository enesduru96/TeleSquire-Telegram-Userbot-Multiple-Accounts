import json
class Config:
    def __init__(self):
        self.config_file = "data/config.json"
        self.config_data = self.load_config()

        self.app_name = self.config_data['app_name']
        self.debug = self.config_data['debug']
        self.database = self.config_data['database']
        self.logging = self.config_data['logging']
        self.api_id = self.config_data['tg_api_id']
        self.api_hash = self.config_data['tg_api_hash']
        self.proxy_type = self.config_data['proxy_type']

    def load_config(self):
        try:
            with open(self.config_file, 'r') as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            print(f"Config file {self.config_file} not found.")
            return {}
        except json.JSONDecodeError:
            print(f"Error decoding JSON in config file {self.config_file}.")
            return {}

    def get_database_url(self):
        return self.database.get('url')

    def get_logging_settings(self):
        return self.logging

    def is_debug_mode(self):
        return self.debug
    
    def get_api_id(self):
        return self.api_id

    def get_api_hash(self):
        return self.api_hash

    def get_proxy_type(self):
        return self.proxy_type