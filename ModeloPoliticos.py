import sklearn.externals
import sklearn.linear_model
import sklearn.preprocessing
import sklearn.cross_validation
import sklearn.pipeline
from scipy.spatial.distance import cosine as cosine_similarity
import json
import numpy as np
import sklearn.metrics


class ModeloPolitico:
    def __init__(self):
        pass

    def carrega_dataset(self, arq_matriz, arq_resumo, arq_modelo_vetorial):
        with open(arq_resumo) as resumo:
            self.resumo_politicos = json.load(resumo)
        self.matriz = sklearn.externals.joblib.load(arq_matriz)
        self.modelo_vetorial = sklearn.externals.joblib.load(arq_modelo_vetorial)
        print("Tudo Carregado")

    def prepara_dataset(self):
        target = list()
        nomes_politicos = list()
        ids_discursos_utilizados = list()

        classe_atual = 0
        for politico in self.resumo_politicos:
            discursos = self.resumo_politicos[politico]['discursos']
            if len(discursos) < 20:
                continue

            nomes_politicos.append(politico)

            for discurso in discursos:
                id_discurso = discurso['idDiscurso']

                target.append(classe_atual)
                ids_discursos_utilizados.append(id_discurso)

            classe_atual += 1
        dataset = self.matriz[ids_discursos_utilizados,:]
        target = np.array(target)

        return dataset, target, nomes_politicos

    def gera_modelo_politico(self, arq_modelo_aprendido):
        dataset, target, nomes_politicos = self.prepara_dataset()
        print(np.unique(target).shape)

        treino, teste, treino_target, teste_target = sklearn.cross_validation.\
            train_test_split(dataset, target, test_size=0.2, stratify=target)

        normalizador = sklearn.preprocessing.MaxAbsScaler()
        modelo = sklearn.linear_model.LogisticRegressionCV(multi_class='multinomial', Cs=[20, 10,], cv=5,
                                                           refit=True, n_jobs=-1, verbose=1,
                                                           class_weight='balanced', solver='lbfgs')
        # self.pipeline = sklearn.pipeline.Pipeline([("normalizador_zscore", normalizador),
        #                                            ('regressao_logisitica', modelo)])

        print("Treinando...")
        # self.pipeline.fit(treino, treino_target)
        modelo.fit(normalizador.fit_transform(treino), y=treino_target)

        print("Treinado")
        # predicao = self.pipeline.predict(teste)
        predicao = modelo.predict(normalizador.transform(teste))
        print(predicao)

        print(sklearn.metrics.classification_report(teste_target, predicao, target_names=nomes_politicos))

        sklearn.externals.joblib.dump(modelo, arq_modelo_aprendido)
        print("Modelo Aprendido Salvo")

        self.matriz_similaridade_politicos(modelo.coef_, nomes_politicos, "comparativo.txt")

    def matriz_similaridade_politicos(self, coefs, nomes_politicos, arq_comparativo):
        n_politicos = len(nomes_politicos)
        similaridades = np.ones((n_politicos, n_politicos))

        for id_politico1 in range(n_politicos):
            for id_politico2 in range(id_politico1 + 1, n_politicos):
                vet1 = coefs[id_politico1, :]
                vet1 = vet1/np.linalg.norm(vet1)

                vet2 = coefs[id_politico2, :]
                vet2 = vet2/np.linalg.norm(vet2)

                similaridade = np.inner(vet1, vet2)
                similaridades[id_politico1, id_politico2] = similaridade
                similaridades[id_politico2, id_politico1] = similaridade

        with open(arq_comparativo, 'w') as f:
            for id_politico in range(n_politicos):
                top_ids = np.argsort(similaridades[:, id_politico]).tolist()[::-1][1:10]
                f.write(nomes_politicos[id_politico])
                f.write("\n=====================\n")
                for i in top_ids:
                    f.write(str(similaridades[id_politico, i]) + " " + nomes_politicos[i] + "\n")
                f.write("\n")

        return similaridades


if __name__ == "__main__":
    prefixo = "saida_resumo_tfidf_sem_norma_stemmer/"
    modelo = ModeloPolitico()
    modelo.carrega_dataset(prefixo + "matriz",
                           prefixo + "resumo_discursos.json",
                           prefixo + "modelo" )
    modelo.gera_modelo_politico(prefixo + "modelo_aprendido")


