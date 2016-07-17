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

        # treino, teste, treino_target, teste_target = sklearn.cross_validation.\
        #     train_test_split(dataset, target, test_size=0.2, stratify=target)

        treino, treino_target = dataset, target

        normalizador = sklearn.preprocessing.MaxAbsScaler()
        regressao = sklearn.linear_model.\
            LogisticRegressionCV(multi_class='ovr', Cs=[50, 10, 1, 0.1], cv=5,
                                 refit=True, n_jobs=-1, verbose=1, class_weight='balanced',
                                 solver='lbfgs')

        print("Treinando...")
        regressao.fit(normalizador.fit_transform(treino), treino_target)
        self.modelo_final = regressao.coef_
        self.salva_artefatos(raiz)

        print(regressao.C_)

        print("REPORT TREINO")
        predicao_treino = regressao.predict(normalizador.transform(treino))
        print(sklearn.metrics.classification_report(treino_target, predicao_treino, target_names=self.ordem_politicos))

        # print("REPORT TESTE")
        # predicao_teste = regressao.predict(normalizador.transform(teste))
        # print(sklearn.metrics.classification_report(teste_target, predicao_teste, target_names=self.ordem_politicos))

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(self, raiz, ["ordem_politicos", "modelo_final"])

if __name__ == "__main__":
    modelo = ModeloPolitico()
    modelo.gera_modelo_politico('teste_final', 20)
