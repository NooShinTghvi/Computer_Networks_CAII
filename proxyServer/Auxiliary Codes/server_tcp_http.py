# importing the requests library 
import requests
import json

r = requests.get('https://github.com/timeline.json')
print(type(r))
#print (json.dumps(r, indent = 4, separators = (". ", " = ")))