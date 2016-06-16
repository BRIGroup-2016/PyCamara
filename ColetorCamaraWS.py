import queue
import threading
import CamaraWS
import time
import datetime
import base64
import subprocess
import json
from bs4 import BeautifulSoup

FORMATO_DATA = "%d/%m/%y"
N_MAX_DIAS_INTERVALO = 360


def forca_lista(elem):
        """
            Método auxiliar
        """
        if type(elem) is not list:
            return [elem]
        return elem


def intervalo_datas(data_inicio, data_fim):
        datetime_corrente = datetime.datetime.strptime(data_inicio, FORMATO_DATA)
        datetime_fim = datetime.datetime.strptime(data_fim, FORMATO_DATA)
        intervalos = list()
        while True:
            inicio_periodo = datetime_corrente.strftime(FORMATO_DATA)

            datetime_corrente += datetime.timedelta(N_MAX_DIAS_INTERVALO)
            if datetime_corrente > datetime_fim:
                intervalos += [(inicio_periodo, data_fim)]
                break

            fim_periodo = datetime_corrente.strftime(FORMATO_DATA)
            intervalos.append((inicio_periodo, fim_periodo))
            datetime_corrente += datetime.timedelta(1)
        return intervalos


def converte_rtf_base64(discurso64):
    rtf = base64.b64decode(discurso64)
    html_text = subprocess.run(["unrtf"], input=rtf, stdout=subprocess.PIPE).stdout.decode('utf-8')
    soup = BeautifulSoup(html_text, 'html.parser')
    texto_puro = soup.get_text()
    texto_puro = texto_puro.strip()
    return texto_puro


class ColetorCamaraWS:
    def __init__(self, n_threads=20, nome_arquivo_resultado=None, intervalo_inicial=1.0,
                 fator_bloqueio=2.0, fator_aceitacao=0.9, intervalo_estatisticas=2.0,
                 max_tentativas=10):
        self.fila_servico = queue.Queue()
        self.fila_escrita = queue.Queue()

        self.n_threads = n_threads
        if nome_arquivo_resultado is None:
            self.nome_arquivo_resultado = "coleta_%s.json" % datetime.datetime.today().strftime("%d-%m-%Y_%H_%M_%S")
        else:
            self.nome_arquivo_resultado = nome_arquivo_resultado
        self.produtores_trabalhando = 0
        self.intervalo_chamada = intervalo_inicial
        self.fator_bloqueio = fator_bloqueio
        self.fator_aceitacao = fator_aceitacao
        self.intervalo_estatisticas = intervalo_estatisticas
        self.max_tentativas = max_tentativas

    def __thread_escrita(self):
        with open(self.nome_arquivo_resultado, 'a') as arquivo:
            while self.produtores_trabalhando > 0:
                try:
                    elem = self.fila_escrita.get(timeout=5)
                except:
                    continue  # se deu timeout, reverificar a condicao

                arquivo.write(json.dumps(elem))
                arquivo.write("\n")
                arquivo.flush()
        print("Feito")

    def __thread_discurso(self):
        intervalo_corrente = self.intervalo_chamada
        while not self.fila_servico.empty():
            discurso = self.fila_servico.get()

            cod_sessao = discurso['codigoSessao']
            num_orador = discurso['numeroOrador']
            num_quarto = discurso['numeroQuartoDiscurso']
            num_insercao = discurso['numeroInsercaoDiscurso']

            try:
                retorno = CamaraWS.obterInteiroTeorDiscursosPlenario(cod_sessao, num_orador, num_quarto, num_insercao)
                discurso64 = retorno['discursoRTFBase64']
                texto_discurso = converte_rtf_base64(discurso64)
                discurso["textoDiscurso"] = texto_discurso

                self.fila_escrita.put(discurso)

                # Caso tenha sido bloqueado anteriormente, porém parei de ser bloqueado, diminuo meu tempo de espera
                if intervalo_corrente > self.intervalo_chamada:
                    intervalo_corrente *= self.fator_aceitacao

            except Exception as e:
                if e == "Bloqueado":
                    # Em caso de bloqueio (403), dobro meu intervalo e tento este caso novamente mais tarde
                    intervalo_corrente *= self.fator_bloqueio
                    self.fila_servico.put(discurso)
                else:
                    # Caso não tenha sido encontrado, registro este erro no arquivo de saida tambem
                    if 'n_tentativas' in discurso:
                        discurso['n_tentativas'] += 1
                    else:
                        discurso['n_tentativas'] = 1

                    if discurso['n_tentativas'] > self.max_tentativas:
                        discurso['erro'] = str(e)
                        self.fila_escrita.put(discurso)
                    else:
                        self.fila_servico.put(discurso)

            time.sleep(intervalo_corrente)

        self.produtores_trabalhando -= 1

    def coletar_teor_discurso(self, dataInicio, dataFim):
        intervalos = intervalo_datas(dataInicio, dataFim)

        # "desnormalizo" a lista para facilitar manipulacoes futuras
        for inicio, fim in intervalos:
            sessoes = CamaraWS.listarDiscursosPlenario(inicio, fim)['sessoesDiscursos']['sessao']
            for sessao in sessoes:
                for fase_sessao in forca_lista(sessao['fasesSessao']['faseSessao']):
                    for discurso in forca_lista(fase_sessao['discursos']['discurso']):
                        fala_discurso = dict()
                        fala_discurso['codigoSessao'] = sessao['codigo']
                        fala_discurso['numeroOrador'] = discurso['orador']['numero']
                        fala_discurso['numeroQuartoDiscurso'] = discurso['numeroQuarto']
                        fala_discurso['numeroInsercaoDiscurso'] = discurso['numeroInsercao']

                        fala_discurso['dataSessao'] = sessao['data']
                        fala_discurso['tipoSessao'] = sessao['tipo']
                        fala_discurso['descricaoFaseSessao'] = fase_sessao['descricao']

                        fala_discurso['nomeOrador'] = discurso['orador']['nome']
                        fala_discurso['partidoOrador'] = discurso['orador']['partido']
                        fala_discurso['ufOrador'] = discurso['orador']['uf']

                        fala_discurso['horaInicioDiscurso'] = discurso['horaInicioDiscurso']
                        fala_discurso['txtIndexacaoDiscurso'] = discurso['txtIndexacao']
                        fala_discurso['sumarioDiscurso'] = discurso['sumario']

                        self.fila_servico.put(fala_discurso)

        ultimo_tam_fila = self.fila_servico.qsize() # depuracao

        # dispara threads
        self.produtores_trabalhando = self.n_threads
        for i in range(self.n_threads):
            t = threading.Thread(target=self.__thread_discurso)
            t.start()

        # dispara thread de escrita
        thread_escrita = threading.Thread(target=self.__thread_escrita)
        thread_escrita.start()

        # estimativa de termino
        consultas_realizadas = 0
        while not self.fila_servico.empty():
            time.sleep(self.intervalo_estatisticas)

            tamanho_corrente = self.fila_servico.qsize()
            delta_consultas = ultimo_tam_fila - tamanho_corrente
            vazao = delta_consultas/self.intervalo_estatisticas
            if vazao == 0:
                continue

            # Calcula estimativa de termino baseado na vazao
            segundos_estimados_fim = tamanho_corrente/vazao
            estimativa_termino = datetime.datetime.now() + datetime.timedelta(seconds = segundos_estimados_fim)

            # Atualiza estatísticas
            consultas_realizadas += delta_consultas
            ultimo_tam_fila = tamanho_corrente

            print("Total = %s (%s consultas/segundo). Término em %s"
                  % (consultas_realizadas, vazao, estimativa_termino))
        thread_escrita.join()

if __name__ == "__main__":
    c = ColetorCamaraWS(n_threads=20)
    c.coletar_teor_discurso(dataInicio = "1/1/10", dataFim = "31/12/14")