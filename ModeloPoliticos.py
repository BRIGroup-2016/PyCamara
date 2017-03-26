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

    def __label_politico(self, metadado):
        return "_".join([metadado["nomeOrador"], metadado["partidoOrador"], metadado["ufOrador"]])

    def __label_partido(self, metadado):
        return metadado["partidoOrador"]

    def __carrega_dataset(self, raiz, n_minimo_discursos, funcao_agregacao):
        self.dados = PipelineUtils.carrega_objetos(raiz, ["vetores", "metadado_discursos"])
        responsaveis = [funcao_agregacao(meta) for meta in self.dados["metadado_discursos"]]

        # Logica para excluir categorias com muito poucas falas
        contador = collections.Counter(responsaveis)
        ids_validos = [i for i in range(len(responsaveis)) if contador[responsaveis[i]] > n_minimo_discursos]
        responsaveis = [responsaveis[id] for id in ids_validos]

        dataset = self.dados["vetores"]
        dataset = dataset[ids_validos, :]

        label_encoder = sklearn.preprocessing.LabelEncoder()
        target = label_encoder.fit_transform(responsaveis)
        significado_labels = label_encoder.classes_

        print("Tudo Carregado")
        print("Dataset Original:", self.dados["vetores"].shape)
        print("Dataset:", dataset.shape)
        print("Target:", target.shape)

        return dataset, target, significado_labels

    def __gera_modelo(self, raiz, n_minimo_discursos, agrupamento='politico'):
        if agrupamento == 'partido':
            funcao_agregacao = self.__label_partido
        else:
            funcao_agregacao = self.__label_politico

        dataset, target, significado_labels = self.__carrega_dataset(raiz, n_minimo_discursos, funcao_agregacao)

        # Não tenho interesse em ter um conjunto de teste, já que as avaliações são qualitativas
        treino, treino_target = dataset, target

        normalizador = sklearn.preprocessing.MaxAbsScaler()
        regressao = sklearn.linear_model. \
            LogisticRegressionCV(multi_class='multinomial', Cs=[10, 1, 0.1], cv=3,
                                 refit=True, n_jobs=-1, verbose=1,  # class_weight='balanced',
                                 solver='lbfgs')

        print("Treinando", agrupamento)
        regressao.fit(normalizador.fit_transform(treino), treino_target)

        print("C:", regressao.C_)
        for classe, scores in regressao.scores_.items():
            print("Classe:", significado_labels[classe], "C:", regressao.C_[classe], scores.max())

        print("REPORT TREINO:")
        predicao_treino = regressao.predict(normalizador.transform(treino))
        print(sklearn.metrics.classification_report(treino_target, predicao_treino, target_names=significado_labels))
        return regressao.coef_, significado_labels

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(self, raiz, ["modelo_partido", "nome_partidos", "modelo_politico", "nome_politicos"])
        # PipelineUtils.salva_objeto(self, raiz, ["modelo_partido", "nome_partidos"])

    def gera_modelos(self, raiz, n_minimo_discursos):
        self.modelo_politico, self.nome_politicos = self.__gera_modelo(raiz, n_minimo_discursos, 'politico')
        self.modelo_partido, self.nome_partidos = self.__gera_modelo(raiz, n_minimo_discursos, 'partido')
        self.salva_artefatos(raiz)

if __name__ == "__main__":
    modelo = ModeloPolitico()
    modelo.gera_modelos('teste_final', 50)
