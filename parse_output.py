import json
import sys

while True:
    try:
        line = input()
    except EOFError:
    # no more information
        break

data=json.loads(line)
print(data[sys.argv[1]])
