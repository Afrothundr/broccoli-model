import json
import os

with open ('Result_23.json') as user_file:
    parsed = json.load(user_file)

rows = []
for item in parsed:
  rows.append(json.dumps({'text': item['agg']['text']}))

with open(f'examples/data/23.jsonl', 'w') as out_file:
    out_file.write('\n'.join(rows))