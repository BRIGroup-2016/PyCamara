import re

__sujeito = re.compile("[OA] SR[A]?\.(.*?)-", re.IGNORECASE | re.LOCALE)
__dispensa_ata = re.compile("As notas taquigráficas desta Sessão Não Deliberativa Solene poderão ser solicitadas"
                          " ao Departamento de Taquigrafia, Revisão e Redação - DETAQ", re.IGNORECASE)
__pronunciamento_encaminhado = re.compile("(DOCUMENTO A QUE SE REFERE O ORADOR|PRONUNCIAMENTO ENCAMINHADO).*?\n", re.IGNORECASE)
__ato_presidencia = re.compile("Ato da Presidência", re.IGNORECASE)
__texto_parentesis = re.compile('\(.*?\)')
__espacos = re.compile('[ \n\xa0]+')

def trata_nome(nome):
    if nome is not None:
        return __texto_parentesis.sub(" ", nome).strip().upper()

def __trata_texto(texto):
    texto = __espacos.sub(" ", texto)
    return texto

def limpa_texto(texto, nome_orador):
    texto = __texto_parentesis.sub(" ", texto)
    if nome_orador is None or __dispensa_ata.search(texto):
        return None

    orador_eh_presidente =  "PRESIDENTE" in nome_orador or "PRESIDENTA" in nome_orador
    if __ato_presidencia.search(texto) and orador_eh_presidente:
        return None

    nome_orador = trata_nome(nome_orador)

    ultimo_match = None
    ultima_pessoa = None

    dialogo = []
    for match_obj in __sujeito.finditer(texto):
        if ultimo_match is not None:
            # senao for o primeiro nome, pego o texto
            inicio_match = match_obj.start()

            fala = texto[ultimo_match: inicio_match].strip()
            fala = __trata_texto(fala)

            dialogo += [(trata_nome(ultima_pessoa), fala)]

        # preparo proxima iteracao
        ultima_pessoa = match_obj.group(1).strip()
        ultimo_match = match_obj.end()

        if (ultima_pessoa == "PRESIDENTE" or ultima_pessoa == "PRESIDENTA") and orador_eh_presidente:
            ultima_pessoa = nome_orador

    # se existir pronunciamento
    pronunciamento_match = __pronunciamento_encaminhado.search(texto)
    if pronunciamento_match is not None:
        fala = texto[ultimo_match:pronunciamento_match.start()].strip()
        fala = __trata_texto(fala)

        dialogo += [(trata_nome(ultima_pessoa), fala)]

        # trato pronunciamento
        pronunciamento = texto[pronunciamento_match.end():].strip()
        pronunciamento = __trata_texto(pronunciamento)

        dialogo += [(nome_orador, pronunciamento)]
    else:
        fala = texto[ultimo_match:]
        fala = __trata_texto(fala)

        dialogo += [(ultima_pessoa, fala)]

    lista_discurso = [ fala for pessoa, fala in dialogo if fala is not None and nome_orador == pessoa]
    discurso = " ".join(lista_discurso)
    return discurso
