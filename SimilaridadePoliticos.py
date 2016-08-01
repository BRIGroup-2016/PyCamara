import PipelineUtils
import numpy as np
import sklearn.manifold
import sklearn.decomposition
import json


def similaridade_cosseno(vetor1, vetor2):
    return np.dot(vetor1, vetor2)


def normaliza_linhas_matriz(matriz):
    normas = np.linalg.norm(matriz, axis=1)
    return np.divide(matriz, normas.reshape((normas.shape[0], 1)))


class AnaliseSimilaridade:
    comparativos_padrao = ['concordancia_positiva', 'concordancia_negativa',
                           'discordancia_apenas_principal', 'discordancia_apenas_secundario']

    def __init__(self, funcao_similaridade=similaridade_cosseno):
        self.funcao_similaridade = funcao_similaridade
        self.modelo = None
        self.nome_categorias = None
        self.nome_features = None
        self.matriz_similaridades = None

    def __matriz_similaridade(self):
        n_categorias, _ = np.shape(self.modelo)
        similaridades = np.ones((n_categorias, n_categorias))
        for id1 in range(n_categorias):
            for id2 in range(id1 + 1, n_categorias):
                vetor1 = self.modelo[id1, :]
                vetor2 = self.modelo[id2, :]

                similaridade = self.funcao_similaridade(vetor1, vetor2)

                similaridades[id1, id2] = similaridade
                similaridades[id2, id1] = similaridade

        self.matriz_similaridades = similaridades

    def resumo_similaridade(self, modelo, nome_categorias, nome_features,
                            n_categorias_similares, n_features_similares):
        self.modelo = normaliza_linhas_matriz(modelo)
        self.nome_categorias = nome_categorias
        self.nome_features = nome_features

        self.__matriz_similaridade()

        resumo = dict()
        for id_categoria in range(len(nome_categorias)):
            categoria_corrente = nome_categorias[id_categoria]
            resumo_categoria = dict()

            features_caracterizantes = self.comparacao_features(id_categoria, id_categoria,
                                                                n_features_similares, 'concordancia_positiva')
            features_descaracterizantes = self.comparacao_features(id_categoria, id_categoria,
                                                                   n_features_similares, 'concordancia_negativa')

            resumo_categoria["caracterizantes"] = self.__monta_json(features_caracterizantes)
            resumo_categoria["descaracterizantes"] = self.__monta_json(features_descaracterizantes)

            similares = list()
            similaridade_categorias = self.categorias_similares(id_categoria, n_categorias_similares)
            for id_categoria_similar, nome_categoria_similar, similaridade in similaridade_categorias:
                json_categoria_similar = dict()
                json_categoria_similar['nome'] = nome_categoria_similar
                json_categoria_similar['similaridade'] = similaridade

                for comparativo in self.comparativos_padrao:
                    features_comparadas = self.comparacao_features(id_categoria, id_categoria_similar,
                                                                   n_features_similares, comparativo)
                    json_categoria_similar[comparativo] = self.__monta_json(features_comparadas)
                similares.append(json_categoria_similar)

            resumo_categoria["similares"] = similares
            resumo[categoria_corrente] = resumo_categoria
        return resumo

    def __monta_json(self, comparativo_features):
        return [{"feature": feature, "importancia": importancia} for _, feature, importancia in comparativo_features]

    def comparacao_features(self, id_categoria1, id_categoria2, n_features, comparativo='concordancia_positiva'):
        centroide1 = self.modelo[id_categoria1, :]
        centroide2 = self.modelo[id_categoria2, :]
        if callable(comparativo):
            relevancias = comparativo(centroide1, centroide2)
        elif comparativo == 'concordancia_positiva':
            relevancias = centroide1 + centroide2
        elif comparativo == 'concordancia_negativa':
            relevancias = - (centroide1 + centroide2)
        elif comparativo == 'discordancia_apenas_principal':
            relevancias = centroide1 - centroide2
        elif comparativo == 'discordancia_apenas_secundario':
            relevancias = - centroide1 + centroide2
        else:
            raise Exception("Comparativo invalido")

        ordem_relevancia = np.argsort(relevancias).tolist()
        mais_relevantes = ordem_relevancia[::-1][:n_features]

        features_mais_relevantes = [(i, self.nome_features[i], relevancias[i]) for i in mais_relevantes]
        return features_mais_relevantes

    def categorias_similares(self, categoria_id, n_categorias):
        mais_similares = np.argsort(self.matriz_similaridades[:, categoria_id]).tolist()[::-1][1:n_categorias+1]
        return [(id, self.nome_categorias[id], self.matriz_similaridades[categoria_id, id]) for id in mais_similares]


class AnaliseSimilaridadePolitica:
    def __init__(self):
        pass

    def realiza_analise(self, raiz):
        dados = PipelineUtils.carrega_objetos(raiz, ["nome_politicos", "modelo_politicos",
                                                     "nome_partidos", "modelo_partidos",
                                                     "nome_features", "vocabulario_escolhido"])

        # Features = os tokens processados, preciso saber qual palavra inteligivel representa cada feature de fato
        nome_features = [dados["vocabulario_escolhido"][token] for token in dados["nome_features"]]
        politicos = dados["nome_politicos"]
        partidos = dados["nome_partidos"]
        modelo_politicos = dados["modelo_politicos"]
        modelo_partidos = dados["modelo_partidos"]

        analise_partido = AnaliseSimilaridade()
        json_partidos = analise_partido.resumo_similaridade(modelo_partidos, partidos, nome_features, 10, 10)
        json.dump(json_partidos, open(raiz + "/analise_partido.json", 'w'), ensure_ascii=True, indent=4, sort_keys=True)

        analise_politico = AnaliseSimilaridade()
        json_politicos = analise_politico.resumo_similaridade(modelo_politicos, politicos, nome_features, 10, 10)
        json.dump(json_politicos, open(raiz + "/analise_politicos.json", 'w'), ensure_ascii=True, indent=4, sort_keys=True)

    # def calcula_dispersao_partidos(self, raiz):
    #     # manifold = sklearn.manifold.MDS(n_components=2, metric='precomputed')
    #     # manifold = sklearn.manifold.TSNE(n_components=2, verbose=1, metric='precomputed')
    #     # manifold = sklearn.manifold.SpectralEmbedding(n_components=2, affinity='precomputed')
    #     # self.dispersao_partidos = manifold.fit_transform(2 - (self.similaridades_partidos + 1))
    #
    #     reducao_dimensionalidade = sklearn.decomposition.TruncatedSVD(n_components=2)
    #     self.dispersao_partidos = reducao_dimensionalidade.fit_transform(self.centroides_partidos)
    #
    #     print("Reducao de dimensionalidade realizada")
    #     PipelineUtils.salva_objeto(self, raiz, ["dispersao_partidos", "ordem_partidos"])


if __name__ == "__main__":
    analise = AnaliseSimilaridadePolitica()
    analise.realiza_analise('teste_final')
