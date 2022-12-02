import requests

BASE = "http://127.0.0.1:5000/"
args = {"status": "in progress", "notes":"testing"}

res = requests.get(BASE + "projects/1", args)
print(res.json())