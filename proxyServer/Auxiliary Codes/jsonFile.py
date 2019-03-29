import json
config = json.loads(open('../Json/config.json').read())
print(config["port"])