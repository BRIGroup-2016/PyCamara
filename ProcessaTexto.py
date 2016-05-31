import subprocess
import base64
from bs4 import BeautifulSoup
import re


__author__ = 'gabriel'

sujeito = re.compile("[OA] SR[A]?\.(.*?)-", re.IGNORECASE | re.LOCALE)
dispensa_ata = re.compile("As notas taquigráficas desta Sessão Não Deliberativa Solene poderão ser solicitadas"
                          " ao Departamento de Taquigrafia, Revisão e Redação - DETAQ", re.IGNORECASE)
pronunciamento_encaminhado = re.compile("(DOCUMENTO A QUE SE REFERE O ORADOR|PRONUNCIAMENTO ENCAMINHADO).*?\n", re.IGNORECASE)
ato_presidencia = re.compile("Ato da Presidência", re.IGNORECASE)
texto_parentesis = re.compile('\(.*?\)')
espacos = re.compile('[ \n\xa0]+')

def trata_nome(nome):
    if nome is not None:
        return texto_parentesis.sub(" ", nome).strip().upper()

def trata_texto(texto):
    texto = espacos.sub(" ", texto)
    return texto

def processa_tudao(html_text, objeto):
    soup = BeautifulSoup(html_text, 'html.parser')
    texto_puro = soup.get_text()
    texto_puro = texto_parentesis.sub(" ", texto_puro)

    nome_orador = objeto['nome']
    orador_eh_presidente =  "PRESIDENTE" in nome_orador or "PRESIDENTA" in nome_orador

    if dispensa_ata.search(texto_puro):
        return None

    if ato_presidencia.search(texto_puro) and orador_eh_presidente:
        return None

    nome_orador = trata_nome(nome_orador)

    ultimo_match = None
    ultima_pessoa = None

    dialogo = []
    for match_obj in sujeito.finditer(texto_puro):
        if ultimo_match is not None:
            # senao for o primeiro nome, pego o texto
            inicio_match = match_obj.start()

            fala = texto_puro[ultimo_match: inicio_match].strip()
            fala = trata_texto(fala)

            dialogo += [(trata_nome(ultima_pessoa), fala)]

        # preparo proxima iteracao
        ultima_pessoa = match_obj.group(1).strip()
        ultimo_match = match_obj.end()

        if (ultima_pessoa == "PRESIDENTE" or ultima_pessoa == "PRESIDENTA") and orador_eh_presidente:
            ultima_pessoa = nome_orador

    # se existir pronunciamento
    pronunciamento_match = pronunciamento_encaminhado.search(texto_puro)
    if pronunciamento_match is not None:
        fala = texto_puro[ultimo_match:pronunciamento_match.start()].strip()
        fala = trata_texto(fala)

        dialogo += [(trata_nome(ultima_pessoa), fala)]

        # trato pronunciamento
        pronunciamento = texto_puro[pronunciamento_match.end():].strip()
        pronunciamento = trata_texto(pronunciamento)

        dialogo += [(nome_orador, pronunciamento)]
    else:
        fala = texto_puro[ultimo_match:]
        fala = trata_texto(fala)

        dialogo += [(ultima_pessoa, fala)]

    lista_discurso = [ fala for pessoa, fala in dialogo if fala is not None and nome_orador == pessoa]
    discurso = " ".join(lista_discurso)
    return discurso


if __name__=="__main__":
    with open('resultado.csv') as f:
        for linha in f.readlines():
            objeto = eval(linha)
            if 'discursoRTFBase64' not in objeto:
                continue

            discurso64 = objeto['discursoRTFBase64']
            rtf = base64.b64decode(discurso64)

            html_text = subprocess.run(["unrtf"], input=rtf, stdout=subprocess.PIPE).stdout.decode('utf-8')

            discurso = processa_tudao(html_text, objeto)
            if discurso is None:
                continue

            partido = objeto['partido']
            nome = objeto['nome']
            nome = trata_nome(nome).replace(' ', '_')
            uf = objeto['uf']
            hora = objeto['horaInicioDiscurso']

            nome_arq = "politicos/%s_%s_%s.txt" % (uf, partido, nome)
            with open(nome_arq, 'a') as escrita:
                escrita.write(hora)
                escrita.write(":\n")
                escrita.write(str(discurso))
                escrita.write("\n")