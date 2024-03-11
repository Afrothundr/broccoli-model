# pip install -U spacy
# python -m spacy download en_core_web_sm
import json
from pydantic import BaseModel
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Token
import srsly

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("en_receipt_model")
list = ' '.join(['WHOLE', 'FOODS', 'had', 'medical healthiest Grocery store', 'of CLEMENTINE BAG', '699', 'stole cut come or', '3.49 F', 'CROFT STRAUBRY sir', '4,99 F', '1.19 LB2.49 rib', 'TARE : 01', 'UT', 'BEANS GREEN', '2.96 F', 'ITEM - 4066', 'viral CREAM SODA', '4.99 B', 'ma TOMATO BASIL S', '3.99 F', 'BULK ALMOND BUTTER', '5.77F', 'mica part red grab', '4.231 F', 'be of VAN ark yurt', '1.39 F', 'be of VAN ark yurt',
                '1.39 F', '365 it chunk TUNA', '2.59 F', 'be of VAN ark yurt', '139 E', 'be of VAN ark yurt', '1.39 F', 'inch of inn HOT C', '6.99 F', 'BLACKBERRIES', '3.99 F', 'arm thick old days', '4.99 F', '2.331B2.99 alb', 'TARE - 01', 'it', 'BANANA 06', '2.31 F', 'ITEM i - 94237', 'my', 'BAG REFUND', '10-', 'ITEM : 486408', '46-F', 'item 20% Off bananas', '35', ': Tax e 7.00%', '63.63', 'own TAX', '35 bad'])
print(list)
# data = srsly.read_jsonl('./examples/data/training_data.jsonl')

# data_tuples = ((eg['text'], eg) for eg in data)
# results = []
# for doc, eg in nlp.pipe(data_tuples, as_tuples=True):
#     for index, ent in enumerate(doc.ents):
#         if ent.label_ == 'FOOD':
#             price = '0.00'
#             for next_ent in doc.ents[index:]:
#                 if next_ent.label_ == 'PRICE':
#                     price = next_ent.text
#                     break
#             results.append(json.dumps(
#                 {'food': ent.text.title(), 'price': price}, indent=4))
# print(results)

class ScrapedItem(BaseModel):
    name: str
    price: float
    
data = []
doc = nlp(list)

# for index, ent in enumerate(doc.ents):
#     if ent.label_ == 'FOOD':
#         price = '0.00'
#         for next_ent in doc.ents[index:]:
#             if next_ent.label_ == 'PRICE':
#                 price = next_ent.text
#                 break
#         try:
#             data.append(json.dumps({'name': ent.text,
#                         'price': float(price)}))
#         except:
#             continue
# print(data)

try:
    for index, ent in enumerate(doc.ents):
        if ent.label_ == 'FOOD':
            price = '0.00'
            for next_ent in doc.ents[index:]:
                if next_ent.label_ == 'PRICE':
                    price = next_ent.text
                    break
            try:
                data.append(ScrapedItem(name=ent.text.title(),
                            price=float(price)).model_dump())
            except:
                continue
except:
    print('error')

print(data)


# # Analyze syntax
# print("Noun phrases:", [chunk.text for chunk in doc.noun_chunks])
# print("Verbs:", [token.lemma_ for token in doc if token.pos_ == "VERB"])

# We can use the food categories and the .similarity function to try and categorize foods

# Find named entities, phrases and concepts
# for match_id, start_index, end_index in matcher(doc):
#     print(doc[start_index: end_index])

# for token in doc:
#     if token:
#         print("Found a similarity to vegetable:", token.text, token.similarity(vegetable))``
