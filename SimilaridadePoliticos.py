import PipelineUtils
import numpy as np
import sklearn.manifold
import sklearn.decomposition


class AnaliseSimilaridade:
    def __init__(self):
        pass

    def carrega_modelos(self, raiz):
        self.dados = PipelineUtils.carrega_objetos(raiz, ["ordem_politicos", "modelo_final",
                                                          "ordem_features", "vocabulario_escolhido"])
        self.nome_features = [self.dados["vocabulario_escolhido"][token] for token in self.dados["ordem_features"]]
        self.modelo = self.__normaliza(self.dados["modelo_final"])
        self.politicos = self.dados["ordem_politicos"]

        self.__calcula_matriz_similaridade_politicos()
        self.__calcula_matriz_similaridade_partidos()

    def __normaliza(self, matriz):
        normas = np.linalg.norm(matriz, axis=1)
        return np.divide(matriz, normas.reshape((normas.shape[0], 1)))

    def __calcula_matriz_similaridade_politicos(self):
        n_politicos = len(self.politicos)
        similaridades = np.ones((n_politicos, n_politicos))

        for id_politico1 in range(n_politicos):
            for id_politico2 in range(id_politico1 + 1, n_politicos):
                vetor1 = self.modelo[id_politico1, :]
                vetor2 = self.modelo[id_politico2, :]

                similaridade = self.similaridade(vetor1, vetor2)

                similaridades[id_politico1, id_politico2] = similaridade
                similaridades[id_politico2, id_politico1] = similaridade

        self.similaridades_politicos = similaridades

    def __calcula_matriz_similaridade_partidos(self):
        centroides, partidos = self.__calcula_centroides_partidos()
        n_partidos = len(partidos)
        similaridades = np.ones((n_partidos, n_partidos))

        for id_partido1 in range(n_partidos):
            for id_partido2 in range(id_partido1 + 1, n_partidos):
                vetor1 = centroides[id_partido1, :]
                vetor2 = centroides[id_partido2, :]

                similaridade = self.similaridade(vetor1, vetor2)

                similaridades[id_partido1, id_partido2] = similaridade
                similaridades[id_partido2, id_partido1] = similaridade

        self.similaridades_partidos = similaridades
        self.centroides_partidos = centroides
        self.ordem_partidos = partidos

    def __calcula_centroides_partidos(self):
        centroide = dict()
        partidos = list({p.split("_")[1] for p in self.politicos})

        # "Group by" partido
        for i in range(len(partidos)):
            partido = partidos[i]
            if partido not in centroide:
                centroide[partido] = list()
            centroide[partido] += [self.modelo[i, :]]

        centroides = np.array([np.mean(centroide[p], axis=0) for p in partidos])
        centroides_normalizados = self.__normaliza(centroides)

        return centroides_normalizados, partidos

    def palavras_relevantes(self, id1, id2, n):
        centroide1 = self.modelo[id1, :]
        centroide2 = self.modelo[id2, :]
        relevancias = centroide1 + centroide2

        ordem_relevancia = np.argsort(relevancias).tolist()
        mais_relevantes = ordem_relevancia[::-1][:n]

        palavras_mais_relevantes = [self.nome_features[i] for i in mais_relevantes]
        return palavras_mais_relevantes

    def similaridade(self, vetor1, vetor2):
        return np.dot(vetor1, vetor2)

    def calcula_dispersao_partidos(self, raiz):
        # manifold = sklearn.manifold.MDS(n_components=2, metric='precomputed')
        # manifold = sklearn.manifold.TSNE(n_components=2, verbose=1, metric='precomputed')
        # manifold = sklearn.manifold.SpectralEmbedding(n_components=2, affinity='precomputed')
        # self.dispersao_partidos = manifold.fit_transform(2 - (self.similaridades_partidos + 1))

        reducao_dimensionalidade = sklearn.decomposition.TruncatedSVD(n_components=2)
        self.dispersao_partidos = reducao_dimensionalidade.fit_transform(self.centroides_partidos)

        print("Reducao de dimensionalidade realizada")
        PipelineUtils.salva_objeto(self, raiz, ["dispersao_partidos", "ordem_partidos"])

    def analise_completa_similaridade(self, arq_save, n_similares):
        with open(arq_save, 'w') as debug:
            for politico_id in range(len(self.politicos)):
                top_ids = np.argsort(self.similaridades_politicos[:, politico_id]).tolist()[::-1][1:n_similares]

                debug.write(self.politicos[politico_id])
                debug.write("\n=====================\n")
                debug.write(str(" ".join(self.palavras_relevantes(politico_id, politico_id, 10))))
                debug.write("\n\n")
                for i in top_ids:
                    debug.write(self.politicos[i] + " -> ")
                    debug.write(str(" ".join(self.palavras_relevantes(politico_id, i, 10))))
                    debug.write("\n")
                debug.write("\n")

if __name__ == "__main__":
    analise = AnaliseSimilaridade()
    analise.carrega_modelos('teste_final')
    analise.calcula_dispersao_partidos('teste_final')
    analise.analise_completa_similaridade('teste_final/RESULTADO.txt', 10)
