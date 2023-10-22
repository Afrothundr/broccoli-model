# pip install -U spacy
# python -m spacy download en_core_web_sm
import spacy
from spacy.matcher import Matcher
from spacy.tokens import Token

# Load English tokenizer, tagger, parser and NER
nlp = spacy.load("en_core_web_md")

#Initialize matcher
matcher = Matcher(nlp.vocab)


# Process whole documents
text = ("""= SUTH SLR o vOo. oY T N
“Sﬁﬁgﬂgﬁx BN VEG @QHﬁF g;aggf?/f
PRE-WRAPPED MEAL
Supervisor #3003
PRE -WRAPPED MEAT $3.00 2 F
LEMON LARGE | W
6@ $0.79 EA $4.74 2 F
ONION GREEN W $1.29 2 F
PEPPER BELL RED W
59 2 FOR $3.00 $7.50 2 F
Reg 2/$5.00 Sale 2/$3.00
PEPPER BELL YELLOW  wx &
3@ 2 FOR $3.00 $4.950 2 F
Reg 2/$5.00 Sale 2/$3.00
WETGHED PRODUCE
~ ASPARAGUS GREEN W
2.25 1b @ $4.99/ 1b $11.23 2 F
ONION YIDALIA W
0,55 1b'@ $1,49/ " $1.82 2 F
Rgg'gE.GQ Sale §1.49
SEEDLESS WTRMILN CHN 3 3
,,1. b @ $3.99/ 1b $4.90 2 F
~ SQUASH ZUCCHINI W 3 e
PR R, §199/ 10 $1 2> f""")
        
docs = list(nlp.pipe(text))
vegetable = nlp("vegetable")


# pattern = [{"POS": "ADJ", "OP": "?"}, {"POS": "NOUN"}]

# matcher.add("ITEM-IDENTIFIER", [pattern])



# # Analyze syntax
# print("Noun phrases:", [chunk.text for chunk in doc.noun_chunks])
# print("Verbs:", [token.lemma_ for token in doc if token.pos_ == "VERB"])

#We can use the food categories and the .similarity function to try and categorize foods

# Find named entities, phrases and concepts
# for match_id, start_index, end_index in matcher(doc):
#     print(doc[start_index: end_index])

for token in doc:
    if token:
        print("Found a similarity to vegetable:", token.text, token.similarity(vegetable))