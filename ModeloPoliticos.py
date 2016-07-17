import sklearn.externals
import sklearn.linear_model
import sklearn.preprocessing
import sklearn.cross_validation
import PipelineUtils
import numpy as np
import sklearn.metrics
import collections


class ModeloPolitico:
    def __init__(self):
        pass

    def __carrega_dataset(self, raiz, n_minimo_discursos):
        self.dados = PipelineUtils.carrega_objetos(raiz, ["vetores", "metadado_discursos"])
        responsaveis = ["_".join([meta["nomeOrador"], meta["partidoOrador"], meta["ufOrador"]])
                        for meta in self.dados["metadado_discursos"]]

        # Logica para excluir politicos com muito poucas falas
        contador = collections.Counter(responsaveis)
        ids_validos = [i for i in range(len(responsaveis)) if contador[responsaveis[i]] > n_minimo_discursos]
        responsaveis = [responsaveis[id] for id in ids_validos]

        dataset = self.dados["vetores"]
        dataset = dataset[ids_validos, :]

        label_encoder = sklearn.preprocessing.LabelEncoder()
        target = label_encoder.fit_transform(responsaveis)
        self.ordem_politicos = label_encoder.classes_

        print("Tudo Carregado")
        print("Dataset Original:", self.dados["vetores"].shape)
        print("Dataset:", dataset.shape)
        print("Target:", target.shape)

        return dataset, target

    def gera_modelo_politico(self, raiz, n_minimo_discursos):
        dataset, target = self.__carrega_dataset(raiz, n_minimo_discursos)

        treino, teste, treino_target, teste_target = sklearn.cross_validation.\
            train_test_split(dataset, target, test_size=0.2, stratify=target)

        normalizador = sklearn.preprocessing.MaxAbsScaler()
        regressao = sklearn.linear_model.\
            LogisticRegressionCV(multi_class='multinomial', Cs=[50, 10, 1, 0.1], cv=5,
                                 refit=True, n_jobs=-1, verbose=1, class_weight='balanced',
                                 solver='lbfgs')

        print("Treinando...")
        regressao.fit(normalizador.fit_transform(treino), treino_target)
        self.modelo_final = regressao.coef_
        self.salva_artefatos(raiz)

        print("REPORT TREINO")
        predicao_treino = regressao.predict(normalizador.transform(treino))
        print(sklearn.metrics.classification_report(treino_target, predicao_treino, target_names=self.ordem_politicos))

        print("REPORT TESTE")
        predicao_teste = regressao.predict(normalizador.transform(teste))
        print(sklearn.metrics.classification_report(teste_target, predicao_teste, target_names=self.ordem_politicos))

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(self, raiz, ["ordem_politicos", "modelo_final"])
    #
    #     self.__calcula_matriz_similaridade(self.modelo.coef_)
    #
    # def comparativo(self, arq_comparativo):
    #     n_politicos = len(self.nomes_politicos)
    #     with open(arq_comparativo, 'w') as f:
    #         for id_politico in range(n_politicos):
    #             top_ids = np.argsort(self.similaridade[:, id_politico]).tolist()[::-1][1:10]
    #             f.write(self.nomes_politicos[id_politico])
    #             f.write("\n=====================\n")
    #             for i in top_ids:
    #                 f.write(str(self.similaridade[id_politico, i]) + " " + self.nomes_politicos[i] + "\n")
    #             f.write("\n")
    #
    # def __calcula_matriz_similaridade(self, coefs):
    #     n_politicos, _ = coefs.shape
    #     similaridades = np.ones((n_politicos, n_politicos))
    #
    #     for id_politico1 in range(n_politicos):
    #         for id_politico2 in range(id_politico1 + 1, n_politicos):
    #             vet1 = coefs[id_politico1, :]
    #             vet1 = vet1/np.linalg.norm(vet1)
    #
    #             vet2 = coefs[id_politico2, :]
    #             vet2 = vet2/np.linalg.norm(vet2)
    #
    #             similaridade = np.inner(vet1, vet2)
    #             similaridades[id_politico1, id_politico2] = similaridade
    #             similaridades[id_politico2, id_politico1] = similaridade
    #     self.similaridade = similaridades


if __name__ == "__main__":
    modelo = ModeloPolitico()
    modelo.gera_modelo_politico('novo_teste', 20)
