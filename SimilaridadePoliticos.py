import PipelineUtils
import numpy as np
import sklearn.manifold
import sklearn.decomposition
import sklearn.cluster
import sklearn.metrics
import matplotlib.pyplot as plt
from wordcloud import WordCloud

import collections
import json

IDEOLOGIAS = {
    "PMDB": ["sincretismo político"],
    "PT": ["socialismo democrático", "reformismo", "desenvolvimentismo", "lulismo", "progressismo", "trotskismo"],
    "PSDB": ["social democracia", "liberalismo social"],
    "PP": ["conservadorismo", "populismo", "liberalismo econômico", "conservadorismo liberal", "pega-tudo"],
    "PSB": ["socialismo democrático", "reformismo", "progressismo"],
    "PPS": ["social democracia", "terceira via", "parlamentarismo"],
    "PSC": ["conservadorismo fiscal", "conservadorismo liberal", "conservadorismo social"],
    "PCDOB": ["socialismo democrático", "comunismo", "marxismo-leninismo", "maoísmo", "reformismo", "desenvolvimentismo"],
    "PRB": ["republicanismo", "conservadorismo liberal", "intervencionismo econômico"],
    "PV": ["ambientalismo", "ecologismo", "liberalismo social", "social democracia", "federalismo", "progressismo"],
    "PSD": ["social democracia", "liberalismo econômico", "nacionalismo", "conservadorismo liberal"],
    "PRP": ["republicanismo", "progressismo"],
    "PSL": ["liberalismo social", "liberalismo econômico", "libertarianismo bleeding-heart"],
    "PMN": ["mobilização"],
    "PHS": ["humanismo", "distributismo", "democracia cristã"],
    "PTC": ["trabalhismo", "conservadorismo liberal", "direita cristã"],
    "PSDC": ["democracia cristã", "conservadorismo social", "direita cristã"],
    "PTDOB": ["trabalhismo", "nacionalismo", "getulismo"],
    "SD": ["trabalhismo"],
    "PTN": ["trabalhismo", "nacionalismo"],
    "PRTB": ["trabalhismo", "participalismo", "conservadorismo", "nacionalismo"],
    "PSOL": ["socialismo", "marxismo", "trotskismo", "ecossocialismo"],
    "PROS": ["republicanismo", "pega-tudo", "nacionalismo"],
    "PEN": ["sustentabilidade", "ecologismo"],
    "PPL": ["desenvolvimentismo", "socialismo científico"],
    "PMB": ["direitos da mulher"],
    "REDE": ["social democracia", "ecologismo", "sustentabilidade"],
    "PSTU": ["socialismo", "comunismo", "marxismo-leninismo", "trotskismo"],
    "PCB": ["socialismo", "comunismo", "marxismo-leninismo"],
    "NOVO": ["liberalismo econômico", "libertarianismo"],
    "PCO": ["socialismo", "comunismo", "marxismo-leninismo", "trotskismo"]}

def similaridade_cosseno(vetor1, vetor2):
    return np.dot(vetor1, vetor2)


def normaliza_linhas_matriz(matriz):
    normas = np.linalg.norm(matriz, axis=1)
    return np.divide(matriz, normas.reshape((normas.shape[0], 1)))


class AnaliseSimilaridade:
    comparativos_padrao = ['concordancia_positiva'] #, 'concordancia_negativa',
                           #'discordancia_apenas_principal', 'discordancia_apenas_secundario']

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

    def ideologias(self, descritor):
        if descritor in IDEOLOGIAS:
            return IDEOLOGIAS[descritor]
        if "_" in descritor:
            partido = descritor.split("_")[1]
            return self.ideologias(partido)
        return []

    def clusterizacao(self, nome_categorias):
        X = (self.matriz_similaridades + 1)
        style = ['.', '+', 'o', '*', 'v']
        for i, damping in enumerate(np.arange(0.5, 1, 0.1)):
            silhuetas = []
            preferencias = []
            for preference in np.arange(0.1, 1, 0.05):
                try:
                    affinity_prop = sklearn.cluster.AffinityPropagation(damping=damping, affinity='precomputed',
                                                                        preference=preference)
                    clusters = affinity_prop.fit_predict(X)
                    silhueta = sklearn.metrics.silhouette_score(-1.0*self.matriz_similaridades + 1,
                                                                clusters, metric='precomputed')
                    silhuetas.append(silhueta)
                    preferencias.append(preference)
                except:
                    continue
            plt.plot(preferencias, silhuetas, label="damping= " + str(damping), marker=style[i])
        plt.legend(loc='lower right')
        plt.show()

        preferencia = float(input("Escolha final preferencia: "))
        damping = float(input("Escolha final damping: "))
        affinity_prop = sklearn.cluster.AffinityPropagation(damping=damping, affinity='precomputed',
                                                            preference=preferencia)
        clusters = affinity_prop.fit_predict(X)

        nome_categorias = np.array(nome_categorias)
        for i in np.unique(clusters):
            indice_cluster = np.nonzero(clusters == i)
            representante = nome_categorias[affinity_prop.cluster_centers_indices_[i]]
            print(i, representante)
            print(nome_categorias[indice_cluster])
            c = collections.Counter()
            c.update([ideologia for descritores in nome_categorias[indice_cluster]
                      for ideologia in self.ideologias(descritores)])
            print(c.most_common(3))
            self.word_cloud(self.modelo[indice_cluster, :].sum(axis=1), ["Cluster_" + str(i) + "_" + representante],
                            self.nome_features)
            print("-----------------")

    def word_cloud(self, matriz, nome_categorias, nome_features):
        for i, nome_categoria in enumerate(nome_categorias):
            print(nome_categoria)
            freqs = [(nome_feature, matriz[i, j]) for j, nome_feature in enumerate(nome_features) if matriz[i, j] > 0]
            wordcloud = WordCloud(scale=10).generate_from_frequencies(freqs)
            wordcloud.to_file("wordcloud/" + nome_categoria + ".png")

    def resumo_similaridade(self, tipo, modelo, nome_categorias, nome_features,
                            n_categorias_similares, n_features_similares):
        self.modelo = normaliza_linhas_matriz(modelo)
        self.nome_categorias = nome_categorias
        self.nome_features = nome_features

        self.__matriz_similaridade()
        self.clusterizacao(nome_categorias)

        np.savetxt('saves/%s-modelo.txt' % tipo, modelo)
        np.savetxt('saves/%s-similaridade.txt' % tipo, self.matriz_similaridades)
        open('saves/%s-nome_categorias.json' % tipo, 'w').write(str(nome_categorias))
        open('saves/%s-nome_features.json' % tipo, 'w').write(str(nome_features))

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
        dados = PipelineUtils.carrega_objetos(raiz, ["nome_politicos", "modelo_politico",
                                                     "nome_partidos", "modelo_partido",
                                                     "ordem_features", "vocabulario_escolhido"])

        # Features = os tokens processados, preciso saber qual palavra inteligivel representa cada feature de fato
        nome_features = [dados["vocabulario_escolhido"][token] for token in dados["ordem_features"]]
        politicos = dados["nome_politicos"]
        partidos = dados["nome_partidos"]
        modelo_politicos = dados["modelo_politico"]
        modelo_partidos = dados["modelo_partido"]

        analise_partido = AnaliseSimilaridade()
        json_partidos = analise_partido.resumo_similaridade('partidos', modelo_partidos, partidos, nome_features, 10, 50)
        # json.dump(json_partidos, open(raiz + "/analise_partido.json", 'w'), ensure_ascii=True, indent=4, sort_keys=True)

        analise_politico = AnaliseSimilaridade()
        json_politicos = analise_politico.resumo_similaridade('politicos', modelo_politicos, politicos, nome_features, 10, 50)
        # json.dump(json_politicos, open(raiz + "/analise_politicos.json", 'w'), ensure_ascii=True, indent=4, sort_keys=True)

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
