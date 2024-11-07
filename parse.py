import json
import os

os.environ['DOCTR_MULTIPROCESSING_DISABLE'] = 'TRUE'

# Specify the directory path you want to search
example_text = 'examples/text/0.1.0/'
file_paths = []

# Loop through all files in the directory
for root, dirs, files in os.walk(example_text):
    for file in files:
        file_path = os.path.join(root, file)
        file_paths.append(file_path)

print(f'Processing {len(file_paths)} files')

rows = []
for index, path in enumerate(file_paths):
    print(f'Progress: {(index + 1) / len(file_paths) * 100}%')

    with open(path, 'r') as file:
        content = file.read()
        rows.append(json.dumps({'text': content}))

file_name = 'training_data'

with open(f'examples/data/{file_name}.jsonl', 'w') as out_file:
    out_file.write('\n'.join(rows))
print('Complete')
