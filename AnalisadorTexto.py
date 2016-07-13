import nltk
import unicodedata
import re
import json
import collections
import LimpezaTextoCamara


NLTK_STOPWORDS_PORTUGUES = nltk.corpus.stopwords.words('portuguese')
NLTK_STEMMER = nltk.stem.RSLPStemmer().stem


class Analisador:
    def __init__(self, separa_diacriticos=True, regexp_separador_tokens='[ ]+',
                 regexp_caracteres_validos='[^a-zA-Z ]', stop=set(),
                 stemmer=NLTK_STEMMER, tamanho_minimo_token=2):

        self.stemmer = stemmer
        self.stop = stop
        self.separa_diacriticos = separa_diacriticos
        self.tamanho_minimo_token = tamanho_minimo_token

        self.caracteres_validos = re.compile(regexp_caracteres_validos)
        self.separador_tokens = re.compile(regexp_separador_tokens)

        # if stemmer is not None:
        #     self.stop = {self.preprocessador(self.stemmer(palavra)) for palavra in stop}

    def preprocessador(self, txt):
        txt = txt.lower()
        if self.separa_diacriticos:
            txt = unicodedata.normalize('NFD', txt)
        txt = self.caracteres_validos.sub("", txt)
        return txt

    def analizador(self, txt):
        """
            Retorna uma lista de pares contendo o token pré-processado
            original e o token "stemizado" para futuras análises, caso exista stemming.
        """
        txt = self.preprocessador(txt)
        tokens = self.separador_tokens.split(txt)

        if self.stemmer is not None:
            return [(self.stemmer(token), token) for token in tokens
                    if len(token) >= self.tamanho_minimo_token and token not in self.stop]
        else:
            return [token for token in tokens
                    if len(token) >= self.tamanho_minimo_token and token not in self.stop]


class PreprocessadorDiscursos:
    def __init__(self, analisador=Analisador()):
        self.contador_palavras_por_token = dict()
        self.contador_tokens_por_politico = dict()

        self.discursos_por_politicos = dict()

        self.tokens = list()
        self.analisador = analisador

    def _contabiliza_token(self, token, palavra_original, politico):
        if token not in self.contador_palavras_por_token:
            self.contador_palavras_por_token = collections.Counter()
        self.contador_palavras_por_token[token].update(palavra_original)

        if politico not in self.contador_tokens_por_politico:
            self.contador_tokens_por_politico = collections.Counter()
        self.contador_tokens_por_politico[politico].update(token)

    def carrega_documentos(self, arq_jsons_discursos):
        id_discurso = 0
        id_politico = 0
        self.discursos_por_politicos = dict()
        with open(arq_jsons_discursos) as jsons:
            for linha in jsons:
                # Simples analise do progresso
                if id_discurso % 100 == 0:
                    print(id_discurso)

                discurso_dict = json.loads(linha)

                texto_discurso = discurso_dict.get('sumarioDiscurso')
                partido_orador = discurso_dict.get('partidoOrador')
                uf_orador = discurso_dict.get('ufOrador')
                nome_orador = discurso_dict.get('nomeOrador')

                if not all([texto_discurso, partido_orador, uf_orador, nome_orador]):
                    continue

                texto_limpo = texto_discurso

                # IMPORTANTE: Descomentar quando for usar o discurso completo de fato
                # texto_limpo = LimpezaTextoCamara.limpa_texto(texto_discurso, nome_orador)
                # if texto_limpo is None:
                #     continue

                nome_orador = LimpezaTextoCamara.trata_nome(nome_orador)
                chave = nome_orador + '_' + partido_orador + '_' + uf_orador

                # Estrutura auxiliar para armazenar os discursos
                resumo_discurso = {'idDiscurso': id_discurso,
                                   'descricaoFaseSessao': discurso_dict.get('descricaoFaseSessao'),
                                   'tipoSessao': discurso_dict.get('tipoSessao'),
                                   'sumarioDiscurso': discurso_dict.get('sumarioDiscurso'),
                                   'horaInicioDiscurso': discurso_dict.get('horaInicioDiscurso'),
                                   'texto': texto_limpo}

                # Mantenho uma relacao dos discursos por politico: dicionario "politico" -> "lista de discursos"
                if chave not in self.discursos_por_politicos:
                    self.discursos_por_politicos[chave] = dict()
                    self.discursos_por_politicos[chave]['discursos'] = list()
                self.discursos_por_politicos[chave]['discursos'].append(resumo_discurso)

                # Armazeno um id para cada politico neste dicionario para futuras referencias
                if 'idPolitico' not in self.discursos_por_politicos[chave]:
                    self.discursos_por_politicos[chave]['idPolitico'] = id_politico
                    id_politico += 1

                # Processo e conto os tokens
                tokens_discurso = self.analisador.analizador(texto_limpo)
                for token_processado, token_original in tokens_discurso:
                    self._contabiliza_token(token_processado, token_original, chave)

                self.tokens.append(tokens_discurso)

                # Preparo proxima iteracao
                id_discurso += 1

    def salva_documentos(self, ):
        pass


if __name__ == "__main__":
    pass
