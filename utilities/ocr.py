from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import requests

def ocrUrl(url: str) -> list:
    model = ocr_predictor(pretrained=True)
    img_data = requests.get(url).content
    doc = DocumentFile.from_images(img_data)
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
    return lines
