import json

class Config:
    def __init__(self, data):
        self.data = data
    def __getitem__(self, name):
        return self.get(name)
    def get(self, name):
        item = self.data[name]
        if isinstance(item, (dict, list, tuple)):
            return Config(item)
        return item
    def getRaw(self, name):
        return self.data[name]
    def __getattr__(self, name):
        return self.get(name)
    @staticmethod
    def getJsonConfig(filename):
        configFile = open(filename)
        data = json.load(configFile)
        configFile.close()
        return Config(data)

config = Config.getJsonConfig('config.json')
