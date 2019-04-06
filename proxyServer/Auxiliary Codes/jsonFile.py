import json

config = json.loads(open('../Json/config.json').read())
config["logging"]["name"] = 'nooshin'

cacheFile = open('cache3.json', 'w')
json.dump(config, cacheFile)
cacheFile.close()
