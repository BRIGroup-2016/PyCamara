import PipelineUtils
import AnalisadorTexto
import itertools
import math
import matplotlib.pyplot as plt


class Estatisticas:
    def __init__(self):
        self.dados = dict()
        self.dicionario_tokens = dict()

        self.lista_partidos = list()
        self.lista_politicos = list()
        self.lista_siglas = ["al", "ac", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms", "mg", "pa", "pb",
                              "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"]
        self.lista_estados_capitais = {"acre", "alagoas", "amapa", "amazonas", "bahia", "ceara", "distrito", "federal",
                                       "espirito", "santo", "goias", "maranhao", "mato", "grosso", "mato", "grosso",
                                       "do", "sul", "minas", "gerais", "para", "paraiba", "parana", "pernambuco",
                                       "piaui", "rio", "de", "janeiro", "rio", "grande", "do", "norte", "rio", "grande",
                                       "do", "sul", "rondonia", "roraima", "santa", "catarina", "sao", "paulo",
                                       "sergipe", "tocantins", "rio", "branco", "maceio", "macapa", "manaus",
                                       "salvador", "fortaleza", "brasilia", "vitoria", "goiania", "sao", "luis",
                                       "cuiaba", "campo", "grande", "belo", "horizonte", "belem", "joao", "pessoa",
                                       "curitiba", "recife", "teresina", "natal", "porto", "alegre", "porto", "velho",
                                       "boa", "vista", "florianopolis", "aracaju", "palmas"}

    def carrega_dados(self, raiz):
        self.dados = PipelineUtils.carrega_objetos(raiz, ['contador_palavras_por_token',
                                                          'contador_discursos_por_politico',
                                                          'contador_tokens_por_politico',
                                                          'contador_discursos_por_token'])
        analizador = AnalisadorTexto.Analisador()
        self.lista_politicos = set(itertools.chain.from_iterable([analizador.preprocessador(identificador_politico.split('_')[0]).split(' ')
                                                                   for identificador_politico in
                                                                   self.dados['contador_discursos_por_politico'].keys()]))

        self.lista_partidos = {identificador_politico.split('_')[1].lower() for identificador_politico in
                               self.dados['contador_discursos_por_politico'].keys()}

    def histograma_palavras(self):
        histograma = dict()
        for token, frequencias in self.dados['contador_palavras_por_token'].items():
            # n_ocorrencias_palavra = sum(frequencias.values())
            n_ocorrencias_documentos = self.dados['contador_discursos_por_token'][token]
            palavra_representante = max(frequencias.keys(), key=lambda palavra: frequencias[palavra])

            if palavra_representante in histograma:
                raise Exception("Aconteceu repeticao de token")

            if palavra_representante in self.lista_politicos or palavra_representante in self.lista_partidos \
                    or palavra_representante in self.lista_siglas \
                    or palavra_representante in self.lista_estados_capitais or "orador" in palavra_representante:
                continue

            # histograma[palavra_representante] = n_ocorrencias_palavra
            histograma[palavra_representante] = n_ocorrencias_documentos

            self.dicionario_tokens[palavra_representante] = token
        return histograma

    def _salva_dicionario_escolhido(self, histograma, raiz, freq_max, freq_min):
        tuplas = list(histograma.items())
        tuplas = sorted(tuplas, key=lambda a: a[1])[::-1]
        self.vocabulario_escolhido = {self.dicionario_tokens[t[0]]: t[0] for t in tuplas[freq_min: freq_max]}
        PipelineUtils.salva_objeto(self, raiz, ['vocabulario_escolhido'])

        # APAGAR - HACK RAPIDO
        f = open('escolha_stopwords.txt', 'w')
        for t in tuplas[freq_min: freq_max]:
            f.write(t[0])
            f.write('\n')

    def escolha_iterativa_dicionario(self, raiz):
        hist = est.histograma_palavras()

        tuples = list(hist.items())
        tuples.sort(key=lambda t: t[1])
        tuples = tuples[::-1]

        index_max = 6000
        index_min = 0

        # Modo iterativo de escolha das frequencias de palavras
        while True:
            print(tuples[index_min: index_max])
            plt.plot([math.log(t[1]) for t in tuples[index_min: index_max] if t[1] > 2])
            plt.title("Frequência das palavras nos diferentes discursos")
            plt.xlabel("Ordem de frequência")
            plt.ylabel("log frequência")
            plt.show()
            try:
                _min = int(input("Posicao minima: "))
                _max = int(input("Posicao maxima: "))
                if _min > _max:
                    print("Minimo maior que o maximo.")
                    continue
                index_max = _max
                index_min = _min
            except:
                # self._salva_dicionario_escolhido(hist, raiz, index_max, index_min)
                # print("Vocabulario de tokens salvo")

                # PLOT FINAL
                plt.plot([math.log(t[1], 10) for t in tuples[0: 6000]])
                plt.title("Frequência das palavras nos diferentes discursos")
                plt.xlabel("Ordem de frequência")
                plt.ylabel("log10 da Frequência")
                plt.axvline(x=index_min, color='r')
                plt.axvline(x=index_max, color='r')
                plt.savefig("distribuicao-final-palavras.png")
                break


if __name__ == '__main__':
    est = Estatisticas()
    est.carrega_dados('teste_final')
    est.escolha_iterativa_dicionario('teste_final')
