import PipelineUtils
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import random


def mapa_cores(partidos):
    mapa = dict()
    partidos = set(partidos)
    n_partidos = len(partidos)

    rgb_inicial = np.array([[254], [125], [0]])/255
    rgb_final = np.array([[0], [0], [254]])/255

    distancia = rgb_final - rgb_inicial
    passo = distancia/n_partidos

    cor_atual = rgb_inicial
    for p in partidos:
        mapa[p] = cor_atual
        cor_atual = cor_atual + passo
    return mapa

#
# def centroides(dispersao, partidos):
#     centroide = dict()
#
#     for i in range(len(partidos)):
#         partido = partidos[i]
#         if partido not in centroide:
#             centroide[partido] = list()
#         centroide[partido] += [dispersao[i, :]]
#
#     partidos = list(set(partidos))
#     dispersao = np.array([np.mean(centroide[p], axis=0) for p in partidos])
#
#     return dispersao, partidos

if __name__ == "__main__":
    dados = PipelineUtils.carrega_objetos('teste_final', ['dispersao_partidos', 'ordem_partidos'])
    dispersao = dados['dispersao_partidos']
    partidos = dados['ordem_partidos']

    colormap = mapa_cores(partidos)
    c = [colormap[p] for p in partidos]
    plt.scatter(dispersao[:, 0], dispersao[:, 1], c=c)
    hand = [mpatches.Patch(color=colormap[p], label=p) for p in set(partidos)]
    plt.legend(handles=hand, fontsize=8)
    plt.show()

    for i in range(len(partidos)):
        print("{name: '" + partidos[i] + "',\ndata:[[%s, %s]]" % (dispersao[i, 0], dispersao[i, 1]) + "}, ")
