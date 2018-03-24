
import json


with open("text.txt", encoding="UTF-8") as f:
    j = json.load(f)

print(type(j))
