from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import requests
import mimetypes
from spellchecker import SpellChecker

spell = SpellChecker()
model = ocr_predictor(pretrained=True, resolve_blocks=False)

def ocrUrl(url: str) -> str:
    img_data = requests.get(url).content
    extension, err = mimetypes.guess_type(url)
    doc = []
    if extension == 'application/pdf':
        doc = DocumentFile.from_pdf(img_data)
    else:
        doc = DocumentFile.from_images(img_data)

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
    return ' '.join(lines)
