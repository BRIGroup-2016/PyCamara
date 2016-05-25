import urllib.request
import xml.dom.minidom

__author__ = 'gabriel'

URL_RAIZ = "http://www.camara.gov.br/SitCamaraWS/SessoesReunioes.asmx"
METODO_TEOR_DISCURSO = "/obterInteiroTeorDiscursosPlenario?codSessao=%s&numOrador=%s&numQuarto=%s&numInsercao=%s"

ELEMENTOS_SESSAO_PLENARIO = ["nome", "partido", "uf", "horaInicioDiscurso", "discursoRTFBase64"]

def obterInteiroTeorDiscursosPlenario(cod_sessao, num_orador, num_quarto, num_insercao):
    url = URL_RAIZ + METODO_TEOR_DISCURSO % (cod_sessao, num_orador, num_quarto, num_insercao)
    sessao_dict = dict()
    with urllib.request.urlopen(url) as response:

        codigo_http = response.getcode()
        if codigo_http == 500:
            raise Exception("Bloqueado")

        html = response.read()
        tree = xml.dom.minidom.parseString(html)
        sessao = tree.getElementsByTagName("sessao")[0]

        for elemento in ELEMENTOS_SESSAO_PLENARIO:
            valor_elemento = sessao.getElementsByTagName(elemento)[0].firstChild.nodeValue
            sessao_dict[elemento] = valor_elemento.strip()

    return sessao_dict


if __name__ == "__main__":
    print(obterInteiroTeorDiscursosPlenario('091.2.55.O', '1','3', '289'))