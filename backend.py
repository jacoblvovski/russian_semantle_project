from pymorphy3 import MorphAnalyzer
from gensim.models import KeyedVectors
from russian_tagsets import converters
import numpy as np
from numpy.linalg import norm


morph = MorphAnalyzer()
conv = converters.converter('opencorpora-int', 'ud20')
model = KeyedVectors.load('ruscorp_model.kv', mmap='r')


def vectorize(word):
    lemma = morph.parse(word)[0].normal_form
    tag_ud20 = conv(str(morph.parse(word)[0].tag))
    POS = tag_ud20.split()[0]
    lemma = lemma + '_' + POS
    try:
        return model[lemma]
    except KeyError:
        return None


def cosine(vec1, vec2):
    if vec1 is None or vec2 is None:
        return 0
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1,  vec2) / (norm(vec1) * norm(vec2))
