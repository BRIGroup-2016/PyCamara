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
        self.discursos_por_politicos = None

    def gera_modelo_vetorial(self, arq_jsons_discursos, arq_modelo, arq_vetores, arq_resumo_json):
        vetores = self.vetorizador.fit_transform(self.iterador_documentos(arq_jsons_discursos))
        sklearn.externals.joblib.dump(self.vetorizador, arq_modelo)
        print("Modelo salvo.")
        sklearn.externals.joblib.dump(vetores, arq_vetores)
        print("Matriz salva.")
        self.salva_resumo_discursos(arq_resumo_json)

    def salva_resumo_discursos(self, arq_resumo_json):
        with open(arq_resumo_json, 'w') as arq:
            dump = json.dumps(self.discursos_por_politicos, sort_keys=True)
            arq.write(dump)

    def iterador_documentos(self, arq_jsons_discursos):
        # TODO Refatorar

        i = 0
        self.discursos_por_politicos = dict()
        with open(arq_jsons_discursos) as jsons:
            for linha in jsons:
                # progresso
                if i % 100 == 0:
                    print(i)

                discurso_dict = json.loads(linha)

                texto_discurso = discurso_dict.get('sumarioDiscurso')
                partido_orador = discurso_dict.get('partidoOrador')
                uf_orador = discurso_dict.get('ufOrador')
                nome_orador = discurso_dict.get('nomeOrador')

                if not all([texto_discurso, partido_orador, uf_orador, nome_orador]):
                    continue

                texto_limpo = texto_discurso
                # texto_limpo = LimpezaTextoCamara.limpa_texto(texto_discurso, nome_orador)
                # if texto_limpo is None:
                #     continue

                # estrutura auxiliar 1
                nome_orador = LimpezaTextoCamara.trata_nome(nome_orador)
                chave = nome_orador + '_' + partido_orador + '_' + uf_orador

                resumo_discurso = {'idDiscurso': i,
                                   'descricaoFaseSessao': discurso_dict.get('descricaoFaseSessao'),
                                   'tipoSessao': discurso_dict.get('tipoSessao'),
                                   'sumarioDiscurso': discurso_dict.get('sumarioDiscurso'),
                                   'horaInicioDiscurso': discurso_dict.get('horaInicioDiscurso')}

                if chave not in self.discursos_por_politicos:
                    self.discursos_por_politicos[chave] = []
                self.discursos_por_politicos[chave].append(resumo_discurso)

                yield texto_limpo
                i += 1


if __name__ == "__main__":
    prefixo = "saida_resumo_tfidf_sem_norma_stemmer/"
    arq_modelo = prefixo + "modelo"
    arq_vetores = prefixo + "matriz"
    arq_resumo_json = prefixo + "resumo_discursos.json"

    modelo = ModeloVetorial(use_idf=True, norma=None, analyzer=AnalisadorTexto.Analisador(stemmer = None).analizador)
    modelo.gera_modelo_vetorial("coleta_15-06-2016_23_48_09.json", arq_modelo, arq_vetores, arq_resumo_json)
