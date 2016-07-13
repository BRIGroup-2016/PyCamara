import sklearn
import sklearn.externals
import json
import AnalisadorTexto


ANALISADOR_PADRAO = AnalisadorTexto.Analisador()


class ModeloVetorial:
    def __init__(self, norma='l2', max_features=None, max_df=1.0, min_df=0.0,
                 binary=False, use_idf=True, smooth_idf=True, sublinear_tf=False):
        """ Construtor apenas realiza um wrapping do construtor do sklearn """
        self.vetorizador = sklearn.feature_extraction.text.TfidfVectorizer(
            max_features=max_features, norm=norma, max_df=max_df,
            min_df=min_df, binary=binary, use_idf=use_idf, smooth_idf=smooth_idf,
            sublinear_tf=sublinear_tf)

    def gera_modelo_vetorial(self, arq_jsons_discursos, arq_modelo, arq_vetores, arq_resumo_json):
        vetores = self.vetorizador.fit_transform(iterador)

        sklearn.externals.joblib.dump(self.vetorizador, arq_modelo)
        print("Modelo salvo.")
        sklearn.externals.joblib.dump(vetores, arq_vetores)
        print("Matriz salva.")
        self.salva_resumo_discursos(arq_resumo_json)

    def salva_resumo_discursos(self, arq_resumo_json):
        with open(arq_resumo_json, 'w') as arq:
            dump = json.dumps(self.discursos_por_politicos, sort_keys=True)
            arq.write(dump)

if __name__ == "__main__":
    prefixo = "saida_resumo_tfidf_sem_norma_1024/"
    arq_modelo = prefixo + "modelo"
    arq_vetores = prefixo + "matriz"
    arq_resumo_json = prefixo + "resumo_discursos.json"

    modelo = ModeloVetorial(use_idf=True, norma=None, max_df=0.99, max_features=1024)

    modelo.gera_modelo_vetorial("coleta_15-06-2016_23_48_09.json", arq_modelo, arq_vetores, arq_resumo_json)

    with open(prefixo + "stop.txt", 'w') as stop_arq:
        stop_arq.write("\n".join(modelo.vetorizador.stop_words_))
    with open(prefixo + "features.txt", 'w') as feat_arq:
        feat_arq.write( "\n".join(modelo.vetorizador.get_feature_names()))
