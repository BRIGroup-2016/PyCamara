import sklearn
import sklearn.externals
import json
import LimpezaTextoCamara
import AnalisadorTexto


ANALISADOR_PADRAO = AnalisadorTexto.Analisador()


class ModeloVetorial:
    def __init__(self, analyzer=ANALISADOR_PADRAO.analizador, norma='l2', max_features=None, max_df=1.0, min_df=0.0,
                 binary=False, use_idf=True, smooth_idf=True, sublinear_tf=False):
        """ Construtor apenas realiza um wrapping do construtor do sklearn """
        self.vetorizador = sklearn.feature_extraction.text.TfidfVectorizer(
            analyzer=analyzer, max_features=max_features, norm=norma, max_df=max_df,
            min_df=min_df, binary=binary, use_idf=use_idf, smooth_idf=smooth_idf,
            sublinear_tf=sublinear_tf)

    def gera_modelo_vetorial(self, arq_jsons_discursos, arq_modelo="saida/modelo", arq_vetores="saida/matriz"):
        vetores = self.vetorizador.fit_transform(self.iterador_documentos(arq_jsons_discursos))
        sklearn.externals.joblib.dump(self.vetorizador, arq_modelo)
        print("Modelo salvo.")
        sklearn.externals.joblib.dump(vetores, arq_vetores)
        print("Matriz salva.")

    def iterador_documentos(self, arq_jsons_discursos):
        i = 0
        with open(arq_jsons_discursos) as jsons:
            for linha in jsons:
                i += 1
                if i % 1000 == 0:
                    print(i)

                discurso_dict = json.loads(linha)
                if 'textoDiscurso' not in discurso_dict:
                    continue
                texto_discurso = discurso_dict['textoDiscurso']
                nome_orador = discurso_dict['nomeOrador']
                texto_limpo = LimpezaTextoCamara.limpa_texto(texto_discurso, nome_orador)
                if texto_limpo is None:
                    continue

                yield texto_limpo

if __name__ == "__main__":
    modelo = ModeloVetorial()
    modelo.gera_modelo_vetorial("coleta_15-06-2016_23_48_09.json")
