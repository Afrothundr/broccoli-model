import json
from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os
from spellchecker import SpellChecker

spell = SpellChecker()

os.environ['DOCTR_MULTIPROCESSING_DISABLE'] = 'TRUE'

# Specify the directory path you want to search
example_images = 'examples/images'
file_paths = []
model = ocr_predictor(pretrained=True, resolve_blocks=False)

# Loop through all files in the directory
for root, dirs, files in os.walk(example_images):
    for file in files:
        file_path = os.path.join(root, file)
        file_paths.append(file_path)

print(f'Processing {len(file_paths)} images')

rows = []
for index, path in enumerate(file_paths):
    print(f'Progress: {(index + 1) / len(file_paths) * 100}%')
    doc = DocumentFile.from_images(path)
    result = model(doc)
    # Extract and print the words
    lines = []
    for prediction in result.pages:
        for block in prediction.blocks:
            for line in block.lines:
                words = []
                for word in line.words:
                    has_correction = spell.correction(word.value)
                    words.append(has_correction if has_correction else word.value)
                lines.append(' '.join(words))


    rows.append(json.dumps({'text': ' '.join(lines)}))

file_name = 'training_data'

with open(f'examples/data/{file_name}.jsonl', 'w') as out_file:
    out_file.write('\n'.join(rows))
print('Complete')
