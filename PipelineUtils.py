import json
import sklearn.externals.joblib
import numpy
import scipy.sparse
import os


def checa_numpy(objeto):
    # TODO melhorar teste
    return isinstance(objeto, numpy.ndarray) or scipy.sparse.issparse(objeto)


def salva_objeto(objeto, diretorio_raiz, nomes_atributos):
    if type(nomes_atributos) is str:
        nomes_atributos = list(nomes_atributos)
    if diretorio_raiz[-1] != '/':
        diretorio_raiz += '/'

    if not os.path.exists(diretorio_raiz):
        os.mkdir(diretorio_raiz)

    for nome_atributo in nomes_atributos:
        atributo = vars(objeto)[nome_atributo]

        if not checa_numpy(atributo):
            nome_arq = diretorio_raiz + nome_atributo
            json_atributo = json.dumps(atributo, sort_keys=True)
            with open(nome_arq, 'w') as arq:
                arq.write(json_atributo)
        else:
            sklearn.externals.joblib.dump(atributo, diretorio_raiz + nome_atributo, compress=3)


def carrega_objetos(diretorio_raiz, nomes_arquivos):
    if type(nomes_arquivos) is str:
        nomes_arquivos = list(nomes_arquivos)
    if diretorio_raiz[-1] != '/':
        diretorio_raiz += '/'

    objetos_carregados = dict()
    for nome_arquivo in nomes_arquivos:
        nome_final = diretorio_raiz + nome_arquivo

        local_extensao = nome_arquivo.rfind('.')
        if local_extensao != -1:
            nome_atributo = nome_arquivo[:local_extensao]
        else:
            nome_atributo = nome_arquivo

        try:
            with open(nome_final) as arquivo:
                json_carregado = json.load(arquivo)
                objetos_carregados[nome_atributo] = json_carregado
        except:  # TODO Capturar apenas se for json
            objetos_carregados[nome_atributo] = sklearn.externals.joblib.load(nome_final)

    return objetos_carregados

if __name__ == '__main__':
    class a():
        def __init__(self):
            self.lista = ['e1', 'e2', 'e3']
            self.array = numpy.array([1, 2])
            self.array_esparsa = scipy.sparse.bsr_matrix([1, 2, 3])


    nomes_attr = ['lista', 'array', 'array_esparsa']
    raiz = 'testezao'
    salva_objeto(a(), raiz, nomes_attr)
    res = carrega_objetos(raiz, nomes_attr)
    print(res)
