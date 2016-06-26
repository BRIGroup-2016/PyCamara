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
        self.discursos_por_politicos = dict()

    def gera_modelo_vetorial(self, arq_jsons_discursos, arq_modelo, arq_vetores, arq_resumo_json):
        iterador = self.__carrega_documentos(arq_jsons_discursos)
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

    # def iterador_politico(self):
    #     politicos = list(self.discursos_por_politicos.keys())
    #     politicos.sort(key=lambda x: self.discursos_por_politicos[x]['idPolitico'])
    #     for politico in politicos:
    #         texto_completo = " ".join([discurso['texto']
    #                                    for discurso in self.discursos_por_politicos[politico]['discursos']])
    #         yield texto_completo

    def __carrega_documentos(self, arq_jsons_discursos):
        # TODO Refatorar

        id_discurso = 0
        id_politico = 0
        self.discursos_por_politicos = dict()
        with open(arq_jsons_discursos) as jsons:
            for linha in jsons:
                # progresso
                if id_discurso % 100 == 0:
                    print(id_discurso)

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

                resumo_discurso = {'idDiscurso': id_discurso,
                                   'descricaoFaseSessao': discurso_dict.get('descricaoFaseSessao'),
                                   'tipoSessao': discurso_dict.get('tipoSessao'),
                                   'sumarioDiscurso': discurso_dict.get('sumarioDiscurso'),
                                   'horaInicioDiscurso': discurso_dict.get('horaInicioDiscurso'),
                                   'texto': texto_limpo}

                if chave not in self.discursos_por_politicos:
                    self.discursos_por_politicos[chave] = dict()
                    self.discursos_por_politicos[chave]['discursos'] = list()
                self.discursos_por_politicos[chave]['discursos'].append(resumo_discurso)

                if 'idPolitico' not in self.discursos_por_politicos[chave]:
                    self.discursos_por_politicos[chave]['idPolitico'] = id_politico
                    id_politico += 1

                yield texto_limpo
                id_discurso += 1


if __name__ == "__main__":
    prefixo = "saida_resumo_tfidf_sem_norma_stemmer/"
    arq_modelo = prefixo + "modelo"
    arq_vetores = prefixo + "matriz"
    arq_resumo_json = prefixo + "resumo_discursos.json"

    modelo = ModeloVetorial(use_idf=True, norma=None, max_df=0.99, max_features=256,
                            analyzer=AnalisadorTexto.Analisador().analizador)

    modelo.gera_modelo_vetorial("coleta_15-06-2016_23_48_09.json", arq_modelo, arq_vetores, arq_resumo_json)

    with open(prefixo + "stop.txt", 'w') as stop_arq:
        stop_arq.write("\n".join(modelo.vetorizador.stop_words_))
    with open(prefixo + "features.txt", 'w') as feat_arq:
        feat_arq.write( "\n".join(modelo.vetorizador.get_feature_names()))
