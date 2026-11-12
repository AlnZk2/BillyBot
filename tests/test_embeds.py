from types import SimpleNamespace

from billybot.core.carregador import hex_para_int
from billybot.ui.embeds import FabricaEmbeds

JOGADOR = SimpleNamespace(display_name="Alan", id=1)


def _fabrica(catalogo):
    return FabricaEmbeds(catalogo.temas)


def test_cor_do_tema_da_conversa(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["deuzebio"]
    e = f.no_de_conversa(c, c["nos"]["carta1"], JOGADOR)
    assert e.color.value == hex_para_int(catalogo.temas["criogenia"]["cor"])
    assert "Laboratório criogênico" in e.footer.text


def test_tema_do_no_muda_a_cor_e_o_ambiente(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["deuzebio"]
    alerta = f.no_de_conversa(c, c["nos"]["carta4"], JOGADOR)
    seguro = f.no_de_conversa(c, c["nos"]["final_pacifica"], JOGADOR)
    assert alerta.color.value == hex_para_int(catalogo.temas["alerta"]["cor"])
    assert "Zona de perigo" in alerta.footer.text
    assert seguro.color.value == hex_para_int(catalogo.temas["seguro"]["cor"])
    assert "Área segura" in seguro.footer.text


def test_precedencia_da_cor(catalogo):
    f = _fabrica(catalogo)
    conversa = {"npc": "X", "tema": "criogenia", "cor": "#112233"}
    assert f.resolver_visual(conversa, {})[0] == 0x112233                         # cor da conversa
    assert f.resolver_visual(conversa, {"tema": "alerta"})[0] == hex_para_int("#C1121F")  # tema do nó vence
    assert f.resolver_visual(conversa, {"tema": "alerta", "cor": "#ABCDEF"})[0] == 0xABCDEF  # cor do nó vence tudo


def test_tema_inexistente_cai_no_padrao(catalogo):
    f = _fabrica(catalogo)
    cor, etiqueta = f.resolver_visual({"npc": "X", "tema": "sumiu"}, {})
    assert cor == hex_para_int(catalogo.temas["padrao"]["cor"]) and etiqueta == ""


def test_narracao_em_italico_e_fala_em_citacao(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["stefano"]
    e = f.no_de_conversa(c, c["nos"]["inicio"], JOGADOR)
    assert e.description.startswith("*O homem ergue os olhos, cansado, e ajeita a mochila nas costas.*")
    assert "> Ei, Alan... você também veio lá de baixo, não foi?" in e.description


def test_reacao_abre_a_narracao_do_proximo_no(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["deuzebio"]
    e = f.no_de_conversa(c, c["nos"]["carta2"], JOGADOR, reacao="O velho sorri.")
    assert e.description.startswith("*O velho sorri. A tosse vem forte")


def test_avatar_vira_autor_e_remove_o_titulo(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["deuzebio"]
    com = f.no_de_conversa(c, c["nos"]["carta1"], JOGADOR, avatar_url="attachment://avatar.png")
    sem = f.no_de_conversa(c, c["nos"]["carta1"], JOGADOR)
    assert com.author.name == "Deuzébio Barbosa" and com.author.icon_url == "attachment://avatar.png"
    assert com.title is None
    assert sem.title == "Deuzébio Barbosa" and sem.author.name is None


def test_itens_aparecem_como_campo(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["deuzebio"]
    e = f.no_de_conversa(c, c["nos"]["segredo_2"], JOGADOR, encerrada=True)
    assert e.fields[0].name == "Itens obtidos"
    assert "Código do cofre escondido: 5730" in e.fields[0].value
    assert "Conversa encerrada" in e.footer.text


def test_sem_jogador_o_nome_vira_viajante(catalogo):
    f = _fabrica(catalogo)
    c = catalogo.conversas["stefano"]
    e = f.no_de_conversa(c, c["nos"]["inicio"], None)
    assert "Ei, viajante..." in e.description and "aberta a todos" in e.footer.text


def test_mensagens_do_bot_usam_cores_e_icones_dos_temas(catalogo):
    f = _fabrica(catalogo)
    assert f.erro("Falhou").color.value == hex_para_int(catalogo.temas["erro"]["cor"])
    assert f.erro("Falhou").title.startswith(catalogo.temas["erro"]["icone"])
    assert f.sucesso("Ok").color.value == hex_para_int(catalogo.temas["sucesso"]["cor"])
    assert f.info("Aviso", "texto").description == "texto"


def test_lista_de_conversas_separa_npcs_e_historia(catalogo):
    e = _fabrica(catalogo).lista_de_conversas(catalogo.conversas)
    assert "**NPCs**" in e.description and "**História**" in e.description
    assert "`!deuzebio [@jogador]`" in e.description and "`!prologo [@jogador]`" in e.description


def test_lista_gigante_e_cortada_para_caber_no_discord(catalogo):
    muitas = {f"c{i}": {"descricao": "x" * 100, "tipo": "npc"} for i in range(100)}
    e = _fabrica(catalogo).lista_de_conversas(muitas)
    assert len(e.description) <= 4096
