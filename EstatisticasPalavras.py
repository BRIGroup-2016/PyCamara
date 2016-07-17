import PipelineUtils
import math
import matplotlib.pyplot as plt


class Estatisticas:
    def __init__(self):
        self.dados = dict()
        self.dicionario_tokens = dict()

    def carrega_dados(self, raiz):
        self.dados = PipelineUtils.carrega_objetos(raiz, ['contador_palavras_por_token',
                                                          'contador_discursos_por_politico',
                                                          'contador_tokens_por_politico'])

    def histograma_palavras(self):
        histograma = dict()
        for token, frequencias in self.dados['contador_palavras_por_token'].items():
            ocorrencia_token = sum(frequencias.values())
            palavra_representate = max(frequencias.keys(), key=lambda palavra: frequencias[palavra])

            if palavra_representate in histograma:
                raise Exception("Aconteceu repeticao de token")
            histograma[palavra_representate] = ocorrencia_token
            self.dicionario_tokens[palavra_representate] = token
        return histograma

    def _salva_dicionario_escolhido(self, histograma, raiz, freq_max, freq_min):
        tuplas = list(histograma.items())
        self.vocabulario_escolhido = {self.dicionario_tokens[t[0]]: t[0] for t in tuplas[freq_min: freq_max]}
        PipelineUtils.salva_objeto(self, raiz, ['vocabulario_escolhido'])

    def escolha_iterativa_dicionario(self, raiz):
        hist = est.histograma_palavras()

        tuples = list(hist.items())
        tuples.sort(key=lambda t: t[1])
        tuples = tuples[::-1]

        index_max = len(tuples)
        index_min = 0

        # Modo iterativo de escolha das frequencias de palavras
        while True:
            print(tuples[index_min: index_max])
            plt.plot([math.log(math.log(t[1])) for t in tuples[index_min: index_max] if t[1] > 2])
            plt.title("Log-log frequência de palavras")
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
                self._salva_dicionario_escolhido(hist, raiz, index_max, index_min)
                print("Vocabulario de tokens salvo")
                break


if __name__ == '__main__':
    est = Estatisticas()
    est.carrega_dados('novo_teste')
    est.escolha_iterativa_dicionario('novo_teste')

    # import seaborn
    # import pandas
    # contador = est.dados['contador_discursos_por_politico']
    # politicos = list(contador.keys())
    # politicos.sort(key=lambda x: contador[x])
    # n_discursos = [contador[politico] for politico in politicos]
    # print(n_discursos)
    # dataframe = pandas.DataFrame({"Politico": politicos, "N_discursos": n_discursos})
    # g = seaborn.barplot(data=dataframe, x="Politico", y="N_discursos", orient="v")
    # seaborn.plt.show(g)
