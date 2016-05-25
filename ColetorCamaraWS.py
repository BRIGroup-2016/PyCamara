import queue
import threading
import CamaraWS
import time
import datetime

__author__ = 'gabriel'

class ColetorCamaraWS():
    def __init__(self, nome_arquivo_resultado="resultado.csv", intervalo_inicial = 1.0,
                 fator_bloqueio=2.0, fator_aceitacao = 0.9, intervalo_estatisticas = 2.0):
        self.fila_servico = queue.Queue()
        self.fila_escrita = queue.Queue()
        self.nome_arquivo_resultado = nome_arquivo_resultado
        self.produtores_trabalhando = 0
        self.intervalo_chamada = intervalo_inicial
        self.fator_bloqueio = fator_bloqueio
        self.fator_aceitacao = fator_aceitacao
        self.intervalo_estatisticas = intervalo_estatisticas

    def __thread_escrita(self):
        with open(self.nome_arquivo_resultado, 'a') as arquivo:
            while self.produtores_trabalhando > 0:
                try:
                    elem = self.fila_escrita.get(timeout=5)
                except:
                    continue
                arquivo.write(str(elem))
                arquivo.write("\n")
                arquivo.flush()
        print("Feito")

    def __thread_discurso(self):
        intervalo_corrente = self.intervalo_chamada
        while not self.fila_servico.empty():
            params = self.fila_servico.get()
            try:
                resultado = CamaraWS.obterInteiroTeorDiscursosPlenario(*params)

                # Caso tenha sido bloqueado anteriormente, porém parei de ser bloqueado, diminuo meu tempo de espera
                if intervalo_corrente > self.intervalo_chamada:
                    intervalo_corrente *= self.fator_aceitacao

            except:
                # Em caso de bloqueio, dobro meu intervalo e tento este caso novamente mais tarde
                intervalo_corrente *= self.fator_bloqueio
                self.fila_servico.put(params)

            self.fila_escrita.put(resultado)
            self.fila_servico.task_done()

            time.sleep(intervalo_corrente)

        self.produtores_trabalhando -= 1

    def coletar_teor_discurso(self, lista_discursos, n_threads=10):
        for d in lista_discursos:
            self.fila_servico.put(d)

        self.produtores_trabalhando = n_threads
        for i in range(n_threads):
            t = threading.Thread(target=self.__thread_discurso)
            t.start()

        thread_escrita = threading.Thread(target=self.__thread_escrita)
        thread_escrita.start()

        ultimo_tam_fila = len(lista_discursos)
        consultas_realizadas = 0
        while not self.fila_servico.empty():
            time.sleep(self.intervalo_estatisticas)

            tamanho_corrente = self.fila_servico.qsize()
            delta_consultas = ultimo_tam_fila - tamanho_corrente
            vazao = delta_consultas/self.intervalo_estatisticas

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
    work_load = [('091.2.55.O', '1','3', '289')]*100
    c = ColetorCamaraWS()
    c.coletar_teor_discurso(work_load, n_threads=10)
