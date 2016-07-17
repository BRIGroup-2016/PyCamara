import sklearn
import sklearn.externals
import PipelineUtils
import AnalisadorTexto


ANALISADOR_PADRAO = AnalisadorTexto.Analisador()


class ModeloVetorial:
    def __init__(self, raiz, norma='l2', binary=False, use_idf=True, smooth_idf=True, sublinear_tf=False):
        """ Construtor apenas realiza um wrapping do construtor do sklearn """

        self.dados = PipelineUtils.carrega_objetos(raiz, ["vocabulario_escolhido", 'tokens_processados'])
        vocabulario = self.dados["vocabulario_escolhido"]
        print("Tokens carregados")

        self.vetorizador = sklearn.feature_extraction.text.\
            TfidfVectorizer(vocabulary=vocabulario.keys(), norm=norma, binary=binary, use_idf=use_idf,
                            smooth_idf=smooth_idf, sublinear_tf=sublinear_tf, analyzer=lambda x: x)

    def gera_modelo_vetorial(self, raiz):
        self.vetores = self.vetorizador.fit_transform(self.dados['tokens_processados'])
        self.ordem_features = modelo.vetorizador.get_feature_names()
        print("Features Geradas", "Shape features", self.vetores.shape)
        self.salva_artefatos(raiz)

    def salva_artefatos(self, raiz):
        PipelineUtils.salva_objeto(self, raiz, ["vetores", "ordem_features"])


if __name__ == "__main__":
    raiz = 'teste_final'
    modelo = ModeloVetorial(raiz, sublinear_tf=True, use_idf=False, norma=None)
    modelo.gera_modelo_vetorial(raiz)
