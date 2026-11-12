import itertools

from billybot.core.motor import Sessao, aplicar_variaveis

CATEGORIAS = ["pacifica", "normal", "agressiva"]


def _clicar_abordagem(sessao, abordagem):
    for indice, opcao in sessao.opcoes_visiveis():
        if opcao.get("abordagem") == abordagem:
            return sessao.escolher(indice)
    raise AssertionError(f"sem opção {abordagem} em {sessao.no_atual}")


def _clicar_texto(sessao, trecho):
    for indice, opcao in sessao.opcoes_visiveis():
        if trecho in opcao["texto"]:
            return sessao.escolher(indice)
    raise AssertionError(f"sem opção '{trecho}' em {sessao.no_atual}")


def test_todas_as_243_combinacoes_do_deuzebio(catalogo):
    conversa = catalogo.conversas["deuzebio"]
    for combo in itertools.product(CATEGORIAS, repeat=5):
        sessao = Sessao(conversa)
        for posicao, abordagem in enumerate(combo):
            assert _clicar_abordagem(sessao, abordagem) == (posicao < 4)
        contagem = {c: combo.count(c) for c in CATEGORIAS}
        lideres = [c for c in CATEGORIAS if contagem[c] == max(contagem.values())]
        esperado = lideres[0] if len(lideres) == 1 else "normal"  # empate vira normal
        assert sessao.no_atual == f"final_{esperado}" and sessao.encerrada


def test_dialogo_secreto_com_o_codigo_certo(catalogo):
    sessao = Sessao(catalogo.conversas["deuzebio"])
    _clicar_abordagem(sessao, "normal")
    _clicar_abordagem(sessao, "normal")
    assert any(o["texto"] == "???" for _, o in sessao.opcoes_visiveis())
    _clicar_texto(sessao, "???")
    _clicar_texto(sessao, "Paraíso")
    assert sessao.no_atual == "segredo_1" and len(sessao.opcoes_visiveis()) == 1
    assert sessao.escolher(0) is False
    assert sessao.no_atual == "segredo_2" and sessao.encerrada


def test_codigo_errado_esconde_o_botao_e_preserva_pontos(catalogo):
    sessao = Sessao(catalogo.conversas["deuzebio"])
    _clicar_abordagem(sessao, "pacifica")
    _clicar_abordagem(sessao, "pacifica")
    _clicar_texto(sessao, "???")
    _clicar_texto(sessao, "Éden")
    assert sessao.no_atual == "codigo_errado"
    _clicar_texto(sessao, "Continuar")
    assert sessao.no_atual == "carta3"
    assert not any(o["texto"] == "???" for _, o in sessao.opcoes_visiveis())
    assert sum(sessao.pontos.values()) == 2


def test_encerrar_nao_muda_de_no(catalogo):
    sessao = Sessao(catalogo.conversas["stefano"])
    assert _clicar_texto(sessao, "Preciso ir") is False
    assert sessao.no_atual == "inicio" and sessao.encerrada


def test_humor_inicial_vem_do_json_e_aparece_no_resumo(catalogo):
    sessao = Sessao(catalogo.conversas["prologo"])
    assert sessao.humor == {"medo": 20, "esperanca": 10}
    assert "Humor: medo 20 | esperanca 10" in sessao.resumo()
    # a sessão tem uma cópia: mudar não altera o JSON carregado
    sessao.humor["medo"] = 99
    assert catalogo.conversas["prologo"]["humor"]["medo"] == 20


def test_prologo_alcanca_o_fim_depois_de_qualquer_escolha(catalogo):
    """Percorre o prólogo escolhendo sempre uma opção que ainda não foi usada naquele nó."""
    conversa = catalogo.conversas["prologo"]
    for primeira in range(2):
        sessao = Sessao(conversa)
        sessao.escolher(primeira)
        visitas = {}
        for _ in range(40):
            if sessao.encerrada:
                break
            opcoes = sessao.opcoes_visiveis()
            n = visitas.get(sessao.no_atual, 0)
            visitas[sessao.no_atual] = n + 1
            sessao.escolher(opcoes[n % len(opcoes)][0])
        assert sessao.encerrada, "o prólogo ficou preso em um laço"
        assert sessao.no_atual == "fim_prologo"


def test_codigo_do_cofre_falado_digito_a_digito(catalogo):
    conversa = catalogo.conversas["deuzebio"]
    fala = conversa["nos"]["segredo_2"]["fala"]
    assert "5, 7, 3, 0" in aplicar_variaveis(fala, conversa, "Alan", para_voz=True)
    assert "5730" in aplicar_variaveis(fala, conversa, "Alan")
