import json
import shutil

import jsonschema

from billybot.config import RAIZ
from billybot.core.carregador import Catalogo


def _copiar_dados(tmp_path, nome="data"):
    destino = tmp_path / nome  # uma cópia nova por chamada
    shutil.copytree(RAIZ / "data", destino)
    return destino


def _conversa(**mudancas):
    base = {
        "npc": "Teste",
        "descricao": "Conversa de teste.",
        "inicio": "a",
        "nos": {
            "a": {"narracao": "Olá.", "opcoes": [{"texto": "Fim.", "proximo": None}]},
        },
    }
    base.update(mudancas)
    return base


def _carregar_com(tmp_path, nome, conteudo, subpasta="npcs"):
    dados = _copiar_dados(tmp_path, f"data_{nome}")
    arquivo = dados / subpasta / f"{nome}.json"
    texto = conteudo if isinstance(conteudo, str) else json.dumps(conteudo, ensure_ascii=False)
    arquivo.write_text(texto, encoding="utf-8")
    return Catalogo.carregar(dados)


def test_dados_reais_sem_erros_nem_avisos(catalogo):
    assert catalogo.erros == []
    assert catalogo.avisos == []
    assert {"deuzebio", "stefano", "sobrevivente", "prologo"} <= set(catalogo.conversas)
    assert {"padrao", "criogenia", "alerta", "seguro", "info", "sucesso", "erro"} <= set(catalogo.temas)


def test_tipo_vem_da_subpasta(catalogo):
    assert catalogo.conversas["deuzebio"]["tipo"] == "npc"
    assert catalogo.conversas["prologo"]["tipo"] == "historia"


def test_arquivos_seguem_o_esquema_json(catalogo):
    esquema = json.loads((RAIZ / "data/schema/conversa.schema.json").read_text(encoding="utf-8"))
    esquema_temas = json.loads((RAIZ / "data/schema/temas.schema.json").read_text(encoding="utf-8"))
    for pasta in ("npcs", "story"):
        for arquivo in (RAIZ / "data" / pasta).glob("*.json"):
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            jsonschema.validate(dados, esquema)
    jsonschema.validate(json.loads((RAIZ / "data/temas.json").read_text(encoding="utf-8")), esquema_temas)


def test_json_quebrado_mostra_arquivo_linha_e_coluna(tmp_path):
    cat = _carregar_com(tmp_path, "quebrado", '{\n  "npc": "x",\n  "descricao": \n}')
    assert any("npcs/quebrado.json" in e and "linha" in e and "coluna" in e for e in cat.erros)


def test_arquivo_com_bom_do_windows_e_aceito(tmp_path):
    dados = _copiar_dados(tmp_path)
    (dados / "npcs" / "bom.json").write_bytes(b"\xef\xbb\xbf" + json.dumps(_conversa()).encode("utf-8"))
    assert Catalogo.carregar(dados).erros == []


def test_proximo_inexistente(tmp_path):
    c = _conversa()
    c["nos"]["a"]["opcoes"][0]["proximo"] = "nao_existe"
    cat = _carregar_com(tmp_path, "t", c)
    assert any("nao_existe" in e for e in cat.erros)


def test_tema_inexistente_na_conversa_e_no_no(tmp_path):
    c = _conversa(tema="neon")
    c["nos"]["a"]["tema"] = "vulcao"
    cat = _carregar_com(tmp_path, "t", c)
    assert any("'neon'" in e for e in cat.erros)
    assert any("'vulcao'" in e for e in cat.erros)


def test_cor_invalida(tmp_path):
    cat = _carregar_com(tmp_path, "t", _conversa(cor="vermelho"))
    assert any("#RRGGBB" in e for e in cat.erros)


def test_id_reservado_e_id_invalido(tmp_path):
    cat = _carregar_com(tmp_path, "falar", _conversa())
    assert any("já é um comando" in e for e in cat.erros)
    cat = _carregar_com(tmp_path, "t2", _conversa(id="Nome Errado"))
    assert any("letras minúsculas" in e for e in cat.erros)


def test_id_duplicado(tmp_path):
    cat = _carregar_com(tmp_path, "outro", _conversa(id="deuzebio"))
    assert any("já é usado" in e for e in cat.erros)


def test_resultado_sem_pontuacao_e_abordagem_desconhecida(tmp_path):
    c = _conversa()
    c["nos"]["a"]["opcoes"] = [
        {"texto": "x", "proximo": "@resultado"},
        {"texto": "y", "proximo": None, "abordagem": "pacifica"},
    ]
    cat = _carregar_com(tmp_path, "t", c)
    assert any("@resultado" in e for e in cat.erros)
    assert any("abordagem 'pacifica'" in e for e in cat.erros)


def test_variavel_inexistente_no_texto(tmp_path):
    c = _conversa()
    c["nos"]["a"]["fala"] = "O código é {codigo}."
    cat = _carregar_com(tmp_path, "t", c)
    assert any("{codigo}" in e for e in cat.erros)


def test_formato_da_voz_e_do_humor(tmp_path):
    cat = _carregar_com(
        tmp_path, "t",
        _conversa(voz={"nome": "x", "velocidade": "-20", "tom": "grave"}, humor={"medo": "alto"}),
    )
    assert any("velocidade" in e for e in cat.erros)
    assert any("'tom'" in e for e in cat.erros)
    assert any("humor" in e for e in cat.erros)


def test_botao_com_mais_de_80_caracteres(tmp_path):
    c = _conversa()
    c["nos"]["a"]["opcoes"][0]["texto"] = "x" * 81
    cat = _carregar_com(tmp_path, "t", c)
    assert any("80 caracteres" in e for e in cat.erros)


def test_no_orfao_vira_aviso(tmp_path):
    c = _conversa()
    c["nos"]["sobrando"] = {"narracao": "Ninguém chega aqui."}
    cat = _carregar_com(tmp_path, "t", c)
    assert cat.erros == []
    assert any("sobrando" in a for a in cat.avisos)


def test_arquivo_de_temas_ausente(tmp_path):
    dados = _copiar_dados(tmp_path)
    (dados / "temas.json").unlink()
    assert any("temas.json" in e for e in Catalogo.carregar(dados).erros)


def test_no_sem_saida_vira_aviso(tmp_path):
    c = _conversa()
    c["nos"]["a"]["opcoes"] = [{"texto": "Ir", "proximo": "b"}]
    c["nos"]["b"] = {"narracao": "Só dá voltas.", "opcoes": [{"texto": "Voltar", "proximo": "a"}]}
    cat = _carregar_com(tmp_path, "t", c)
    assert cat.erros == []
    assert any("nunca consegue terminar" in a and "a, b" in a for a in cat.avisos)


def test_resultado_conta_como_saida(tmp_path):
    c = _conversa(pontuacao={"empate": "x", "destinos": {"x": "fim"}})
    c["nos"]["a"]["opcoes"] = [{"texto": "Decidir", "proximo": "@resultado", "abordagem": "x"}]
    c["nos"]["fim"] = {"narracao": "Fim.", "opcoes": []}
    cat = _carregar_com(tmp_path, "t", c)
    assert cat.erros == [] and cat.avisos == []
