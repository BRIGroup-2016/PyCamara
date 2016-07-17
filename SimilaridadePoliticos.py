import PipelineUtils
import numpy as np
import sklearn.manifold
import seaborn
import pandas

class AnaliseSimilaridade:
    def __init__(self):
        pass

    def matriz_similaridade(self):
        n_politicos = len(self.politicos)
        similaridades = np.ones((n_politicos, n_politicos))

        for id_politico1 in range(n_politicos):
            for id_politico2 in range(id_politico1 + 1, n_politicos):
                similaridade = self.similaridade(id_politico1, id_politico2)
                similaridades[id_politico1, id_politico2] = similaridade
                similaridades[id_politico2, id_politico1] = similaridade

        return similaridades

    def palavras_relevantes(self, id1, id2, n):
        centroide1 = self.modelo[id1, :]
        centroide2 = self.modelo[id2, :]
        relevancias = np.multiply(centroide1, centroide2)

        ordem_relevancia = np.argsort(relevancias).tolist()
        mais_relevantes = ordem_relevancia[::-1][:n]

        palavras_mais_relevantes = [self.nome_features[i] for i in mais_relevantes]
        return palavras_mais_relevantes

    def similaridade(self, id1, id2):
        vetor1 = self.modelo[id1]
        vetor2 = self.modelo[id2]
        return np.dot(vetor1, vetor2)

    def __normaliza(self, matriz):
        normas = np.linalg.norm(matriz, axis=1)
        return np.divide(matriz, normas.reshape((normas.shape[0], 1)))

    def carrega_modelos(self, raiz):
        self.dados = PipelineUtils.carrega_objetos(raiz, ["ordem_politicos", "modelo_final",
                                                          "ordem_features", "vocabulario_escolhido"])
        self.nome_features = [self.dados["vocabulario_escolhido"][token] for token in self.dados["ordem_features"]]
        self.modelo = self.__normaliza(self.dados["modelo_final"])
        self.politicos = self.dados["ordem_politicos"]
        self.matriz_similaridades = self.matriz_similaridade()

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(self, raiz, ["dispersao", "partidos"])

    def dispersao_similaridades(self, raiz):
        manifold = sklearn.manifold.TSNE(n_components=2, metric='precomputed')
        self.dispersao = manifold.fit_transform(self.matriz_similaridades + 1)
        print("Reducao de dimensionalidade realizada")
        self.partidos = [politico.split("_")[1] for politico in self.dados["ordem_politicos"]]
        self.salva_artefatos(raiz)

    def analise_completa_similaridade(self, arq_save, n_similares):
        with open(arq_save, 'w') as debug:
            for politico_id in range(len(self.politicos)):
                top_ids = np.argsort(self.matriz_similaridades [:, politico_id]).tolist()[::-1][1:n_similares]

                debug.write(self.politicos[politico_id])
                debug.write("\n=====================\n")

                for i in top_ids:
                    debug.write(self.politicos[i] + " -> ")
                    debug.write(str(" ".join(self.palavras_relevantes(politico_id, i, 10))))
                    debug.write("\n")
                debug.write("\n")

if __name__ == "__main__":
    analise = AnaliseSimilaridade()
    analise.carrega_modelos('novo_teste')
    analise.dispersao_similaridades('novo_teste')
    analise.analise_completa_similaridade('novo_teste/RESULTADO.txt', 10)
