import nltk
import unicodedata
import re
import json
import collections
import LimpezaTextoCamara
import PipelineUtils


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
        self.analisador = analisador

        self.tokens_processados = list()
        self.metadado_discursos = list()

        # Estatisticas
        self.contador_palavras_por_token = dict()
        self.contador_tokens_por_politico = dict()
        self.contador_discursos_por_politico = collections.Counter()

    def _coleta_estatistica(self, token, palavra_original, politico):
        if token not in self.contador_palavras_por_token:
            self.contador_palavras_por_token[token] = collections.Counter()
        self.contador_palavras_por_token[token].update([palavra_original])

        if politico not in self.contador_tokens_por_politico:
            self.contador_tokens_por_politico[politico] = collections.Counter()
        self.contador_tokens_por_politico[politico].update([token])

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(diretorio_raiz=raiz,
                                   nomes_atributos=['metadado_discursos',
                                                    'tokens_processados',
                                                    'contador_palavras_por_token',
                                                    'contador_discursos_por_politico',
                                                    'contador_tokens_por_politico'],
                                   objeto=self)

    def carrega_documentos(self, arq_jsons_discursos):
        id_discurso = 0
        self.metadado_discursos = list()
        self.tokens_processados = list()
        with open(arq_jsons_discursos) as jsons:
            for linha in jsons:
                # Simples analise do progresso
                if id_discurso % 100 == 0:
                    print(id_discurso)
                id_discurso += 1

                discurso_dict = json.loads(linha)
                texto_discurso = discurso_dict.get('textoDiscurso')
                partido_orador = discurso_dict.get('partidoOrador')
                uf_orador = discurso_dict.get('ufOrador')
                nome_orador = discurso_dict.get('nomeOrador')

                # Caso uma das partes necessarias para a análise não exista, ignoro ela
                if not all([texto_discurso, partido_orador, uf_orador, nome_orador]):
                    continue

                # IMPORTANTE: Trecho que seleciona o que será tratado como texto do discurso
                texto_limpo = LimpezaTextoCamara.limpa_texto(texto_discurso, nome_orador)
                if texto_limpo is None:
                    continue
                # TODO Rever quando for usar o discurso completo de fato
                texto_limpo = texto_discurso

                nome_orador = LimpezaTextoCamara.trata_nome(nome_orador)
                identificador_politico = nome_orador + '_' + partido_orador + '_' + uf_orador

                # Estrutura auxiliar para armazenar as informações relevantes dos discursos
                resumo_discurso = {'descricaoFaseSessao': discurso_dict.get('descricaoFaseSessao'),
                                   'tipoSessao': discurso_dict.get('tipoSessao'),
                                   'horaInicioDiscurso': discurso_dict.get('horaInicioDiscurso'),
                                   # 'sumarioDiscurso': partido_orador,
                                   'nomeOrador': nome_orador,
                                   'ufOrador': uf_orador,
                                   'partidoOrador': partido_orador}
                self.metadado_discursos.append(resumo_discurso)

                # Processo e conto os tokens
                tokens_discurso = list()
                for token_processado, token_original in self.analisador.analizador(texto_limpo):
                    self._coleta_estatistica(token_processado, token_original, identificador_politico)
                    tokens_discurso.append(token_processado)

                # Esta Estatistica deve ser coletada fora apenas uma vez por discurso
                self.contador_discursos_por_politico.update([identificador_politico])

                self.tokens_processados.append(tokens_discurso)

if __name__ == "__main__":
    prep = PreprocessadorDiscursos()
    prep.carrega_documentos('coleta_15-06-2016_23_48_09.json')
    prep.salva_artefatos('teste_final')
