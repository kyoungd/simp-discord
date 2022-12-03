import json
from types import SimpleNamespace


class Config(SimpleNamespace):
    def save(self):
        with open(self._filename, "w") as config_file:
            filepath = self._filename
            delattr(self, '_filename')
            json.dump(self.__dict__, config_file, indent=4, default=Config.to_dict)
            self._filename = filepath
    
    def to_dict(c):
        return c.__dict__

def init_config(s: str, filepath: str):
    config = json.loads(s, object_hook=lambda d: Config(**d))
    config._filename = filepath
    return config

def load_config(filepath: str) -> Config:
    with open(filepath, "r") as config_file:
        config = json.load(config_file, object_hook=lambda d: Config(**d))
    config._filename = filepath
    return config
