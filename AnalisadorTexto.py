import nltk
import unicodedata
import re


NLTK_STOPWORDS_PORTUGUES = nltk.corpus.stopwords.words('portuguese')
NLTK_STEMMER = nltk.stem.RSLPStemmer().stem


class Analisador:
    def __init__(self, separa_diacriticos=True, regexp_separador_tokens='[ ]+',
                 regexp_caracteres_validos='[^a-zA-Z ]', stop=NLTK_STOPWORDS_PORTUGUES,
                 stemmer = NLTK_STEMMER, tamanho_minimo_token=2):

        self.stemmer = stemmer
        self.stop = stop
        self.separa_diacriticos = separa_diacriticos
        self.tamanho_minimo_token = tamanho_minimo_token

        self.caracteres_validos = re.compile(regexp_caracteres_validos)
        self.separador_tokens= re.compile(regexp_separador_tokens)

        if stemmer is not None:
            self.stop = {self.preprocessador(self.stemmer(palavra)) for palavra in stop}

    def preprocessador(self, txt):
        txt = txt.lower()
        if self.separa_diacriticos:
            txt = unicodedata.normalize('NFD', txt)
        txt = self.caracteres_validos.sub("", txt)
        return txt

    def analizador(self, txt):
        txt = self.preprocessador(txt)
        tokens = self.separador_tokens.split(txt)

        return [token for token in tokens
                 if len(token) >= self.tamanho_minimo_token and token not in self.stop]