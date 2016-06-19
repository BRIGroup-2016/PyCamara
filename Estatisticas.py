import numpy as np
import json
import sklearn
import sklearn.externals
import sklearn.decomposition
from scipy.spatial.distance import cosine as cosine_similarity
import datetime


FORMATO_DATA_HORA = "%d/%m/%Y %H:%M:%S"


class Estatisticas:
    def __init__(self):
        self.resumo_politicos = dict()
        self.matriz = None

    def carrega_dados(self, arq_resumo, arq_matriz):
        with open(arq_resumo) as resumo:
            self.resumo_politicos = json.load(resumo)
        self.matriz = sklearn.externals.joblib.load(arq_matriz)

        svd = sklearn.decomposition.TruncatedSVD(n_components=50, n_iter=5)
        self.matriz = svd.fit_transform(self.matriz)

        print(len(self.resumo_politicos))

    def analisa_similaridade_politicos(self):
        lista_politicos = [politico for politico in self.resumo_politicos if len(self.resumo_politicos[politico])> 30]
        n_politicos = len(lista_politicos)
        similaridades = np.ones((n_politicos, n_politicos))

        for id_politico1 in range(n_politicos):
            for id_politico2 in range(id_politico1 + 1, n_politicos):
                similaridade = self.__similaridade_politicos(lista_politicos[id_politico1],
                                                             lista_politicos[id_politico2])
                similaridades[id_politico1, id_politico2] = similaridade
                similaridades[id_politico2, id_politico1] = similaridade

        return similaridades, lista_politicos


    def analisa_coerencia(self):
        for politico in self.resumo_politicos:
            # discursos = [(discurso['idDiscurso'], discurso['horaInicioDiscurso'])
            #               for discurso in self.resumo_politicos[politico]]

            discursos = [ datetime.datetime.strptime(discurso['horaInicioDiscurso'], FORMATO_DATA_HORA) for discurso in self.resumo_politicos[politico]]
            # self._ordena_por_data(discursos)
            print(discursos)
            break

    def __similaridade_politicos(self, politico1, politico2):
        ids1 = self.__id_discurso_politico(politico1)
        ids2 = self.__id_discurso_politico(politico2)

        centroide1 = self.matriz[ids1].mean(axis=0)
        centroide1 = centroide1/np.linalg.norm(centroide1)

        centroide2 = self.matriz[ids2].mean(axis=0)
        centroide2 = centroide2/np.linalg.norm(centroide2)

        similaridade = cosine_similarity(centroide1, centroide2)
        return similaridade

    def __id_discurso_politico(self,politico):
        return [discurso['idDiscurso'] for discurso in self.resumo_politicos[politico]]

    def _ordena_por_data(self, discursos):
        sorted(discursos, key=lambda x: datetime.datetime.strptime(x[1], FORMATO_DATA_HORA))

    def __calculo_coerencia(self, vetores_analise, janela):
        n_linhas, _ = vetores_analise.shape
        similaridades = list()

        for i in range(janela, n_linhas):
            contexto = vetores_analise[i-janela:i, :].mean(axis=0)
            atual = vetores_analise[i, :].toarray()

            similaridade = cosine_similarity(contexto, atual)
            similaridades += [similaridade]


if __name__ == '__main__':
    est = Estatisticas()
    prefixo = 'saida_resumo_tfidf_sem_norma_stemmer/'
    est.carrega_dados(prefixo + "resumo_discursos.json", prefixo + "matriz")
    sim, politicos = est.analisa_similaridade_politicos()

    linhas = list()
    for politico_id in range(len(politicos)):
        top_ids = np.argsort(sim[:, politico_id]).tolist()[::-1][1:5]
        linhas.append(politicos[politico_id])
        linhas.append("\n=====================\n")
        for i in top_ids:
            linhas.append(str(sim[politico_id, i]))
            linhas.append(" "+ politicos[i]+"\n")
        linhas.append("\n")

    with open(prefixo + 'similaridades.txt','w') as debug:
        debug.writelines(linhas)
