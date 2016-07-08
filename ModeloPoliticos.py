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

    def gera_modelo_politico(self, arq_modelo_aprendido, arq_matriz_similaridade, arq_nomes_politicos):
        dataset, target, nomes_politicos = self.prepara_dataset()
        self.nomes_politicos = nomes_politicos

        print(np.unique(target).shape)

        treino, teste, treino_target, teste_target = sklearn.cross_validation.\
            train_test_split(dataset, target, test_size=0.2, stratify=target)

        normalizador = sklearn.preprocessing.MaxAbsScaler()
        regressao = sklearn.linear_model.LogisticRegressionCV(multi_class='multinomial', Cs=[30, 10, 1, 0.1], cv=5,
                                                           refit=True, n_jobs=-1, verbose=1,
                                                           class_weight='balanced', solver='lbfgs')
        self.modelo = regressao
        # self.modelo = sklearn.pipeline.Pipeline([("normalizador_zscore", normalizador),
        #                                            ('regressao_logisitica', regressao)])

        print("Treinando...")
        # self.modelo.fit(treino, treino_target)
        regressao.fit(normalizador.fit_transform(treino), y=treino_target)

        print("Treinado")
        # predicao = self.modelo.predict(teste)
        predicao = regressao.predict(normalizador.transform(teste))

        print(sklearn.metrics.classification_report(teste_target, predicao, target_names=nomes_politicos))

        sklearn.externals.joblib.dump(self.modelo, arq_modelo_aprendido)
        sklearn.externals.joblib.dump(normalizador, arq_modelo_aprendido + "_normalizador")
        print("Modelo Aprendido Salvo")

        self.__calcula_matriz_similaridade(self.modelo.coef_)
        sklearn.externals.joblib.dump(self.similaridade, arq_matriz_similaridade)

        with open(arq_nomes_politicos, 'w') as f:
            f.write("\n".join(nomes_politicos))

        print("Matriz de similaridade salva")

    def comparativo(self, arq_comparativo):
        n_politicos = len(self.nomes_politicos)
        with open(arq_comparativo, 'w') as f:
            for id_politico in range(n_politicos):
                top_ids = np.argsort(self.similaridade[:, id_politico]).tolist()[::-1][1:10]
                f.write(self.nomes_politicos[id_politico])
                f.write("\n=====================\n")
                for i in top_ids:
                    f.write(str(self.similaridade[id_politico, i]) + " " + self.nomes_politicos[i] + "\n")
                f.write("\n")

    def __calcula_matriz_similaridade(self, coefs):
        n_politicos, _ = coefs.shape
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
        self.similaridade = similaridades


if __name__ == "__main__":
    prefixo = "saida_resumo_tfidf_sem_norma_512/"
    modelo = ModeloPolitico()
    modelo.carrega_dataset(prefixo + "matriz",
                           prefixo + "resumo_discursos.json",
                           prefixo + "modelo" )
    modelo.gera_modelo_politico(prefixo + "modelo_aprendido", prefixo + "similaridade", prefixo + "politicos")
    modelo.comparativo(prefixo + "comparativo.txt")

