from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import os

os.environ['DOCTR_MULTIPROCESSING_DISABLE'] = 'TRUE'

# Specify the directory path you want to search
example_images = 'examples/images'
file_paths = []

# Loop through all files in the directory
for root, dirs, files in os.walk(example_images):
    for file in files:
        file_path = os.path.join(root, file)
        file_paths.append(file_path)

print(f'Processing {len(file_paths)} images')
for index, path in enumerate(file_paths):
    print(f'Progress: {(index + 1) / len(file_paths) * 100}%')
    model = ocr_predictor(pretrained=True)
    doc = DocumentFile.from_images(path)
    result = model(doc)
    # Extract and print the words
    lines = []
    for prediction in result.pages:
        for block in prediction.blocks:
            for line in block.lines:
                words = []
                for word in line.words:
                    words.append(word.value)
                lines.append(' '.join(words))


    # json_output = result.export()
    file_name = os.path.basename(path)
    name_without_extension, _ = os.path.splitext(file_name)
    with open(f'examples/text/{name_without_extension}.txt', 'w') as out_file:
        out_file.write('\n'.join(lines))
print('Complete')