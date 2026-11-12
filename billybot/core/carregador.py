"""
carregador.py - Lê e valida os arquivos JSON da pasta data/ (item 1).

    data/temas.json        cores e ícones dos embeds (item 2)
    data/npcs/*.json       uma conversa de NPC por arquivo
    data/story/*.json      uma conversa de história/narração por arquivo

O comando no Discord é o "id" do arquivo (ou o nome do arquivo sem ".json").
Erros de digitação nos JSON aparecem com o arquivo, a linha e a coluna.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from billybot.core.motor import RESULTADO

# Nomes que já são comandos do bot: nenhuma conversa pode usá-los como id.
RESERVADOS = frozenset({"help", "conversas", "recarregar", "falar", "vozes", "testarvoz"})

# (subpasta de data/, tipo da conversa)
SUBPASTAS = (("npcs", "npc"), ("story", "historia"))

PADRAO_ID = re.compile(r"^[a-z0-9_]+$")
PADRAO_VARIAVEL = re.compile(r"\{(\w+)\}")
PADRAO_COR = re.compile(r"^#[0-9A-Fa-f]{6}$")
PADRAO_VELOCIDADE = re.compile(r"^[+-]\d+%$")
PADRAO_TOM = re.compile(r"^[+-]\d+Hz$")


def hex_para_int(cor: str) -> int:
    """'#6EC1E4' -> número que o discord.Embed entende."""
    return int(cor.lstrip("#"), 16)


def _ler_json(caminho: Path, rotulo: str, erros: list):
    # utf-8-sig: aceita arquivos salvos pelo Bloco de Notas do Windows (com BOM)
    try:
        with open(caminho, encoding="utf-8-sig") as arquivo:
            return json.load(arquivo)
    except json.JSONDecodeError as erro:
        erros.append(
            f"[{rotulo}] JSON inválido na linha {erro.lineno}, coluna {erro.colno}: {erro.msg}"
        )
    except OSError as erro:
        erros.append(f"[{rotulo}] não consegui abrir o arquivo: {erro}")
    return None


def carregar_temas(caminho: Path, erros: list) -> dict:
    """Lê data/temas.json. Cada tema precisa de 'cor' (#RRGGBB); 'icone' e 'nome' são opcionais."""
    if not caminho.is_file():
        erros.append("[temas.json] arquivo não encontrado na pasta data/.")
        return {}
    bruto = _ler_json(caminho, "temas.json", erros)
    if bruto is None:
        return {}
    if not isinstance(bruto, dict):
        erros.append("[temas.json] precisa ser um objeto com os temas.")
        return {}

    temas = {}
    for chave, tema in bruto.items():
        if chave.startswith("$"):  # "$schema"
            continue
        cor = tema.get("cor") if isinstance(tema, dict) else None
        if not isinstance(cor, str) or not PADRAO_COR.match(cor):
            erros.append(f"[temas.json] o tema '{chave}' precisa de 'cor' no formato #RRGGBB.")
            continue
        temas[chave] = tema
    if "padrao" not in temas:
        erros.append("[temas.json] falta o tema 'padrao'.")
    return temas


def _textos_do_no(no: dict):
    """Gera (campo, texto) de tudo o que o jogador pode ler em um nó."""
    for campo in ("narracao", "fala", "fala_tts", "narracao_final"):
        if isinstance(no.get(campo), str):
            yield campo, no[campo]
    for item in no.get("itens") or []:
        if isinstance(item, str):
            yield "itens", item
    for opcao in no.get("opcoes") or []:
        if not isinstance(opcao, dict):
            continue
        if isinstance(opcao.get("texto"), str):
            yield "opcao", opcao["texto"]
        if isinstance(opcao.get("reacao"), str):
            yield "reacao", opcao["reacao"]


def validar_conversa(chave: str, conversa: dict, temas: dict, origem: str):
    """Confere uma conversa. Retorna (erros, avisos); nunca levanta exceção."""
    erros, avisos = [], []

    def erro(local: str, mensagem: str):
        erros.append(f"[{origem}] " + (f"{local}: " if local else "") + mensagem)

    if not PADRAO_ID.match(chave):
        erro("", f"o id '{chave}' deve ter só letras minúsculas, números e _ (sem espaços ou acentos).")
    if chave in RESERVADOS:
        erro("", f"o id '{chave}' já é um comando do bot. Escolha outro.")
    for campo in ("npc", "descricao"):
        if not isinstance(conversa.get(campo), str) or not conversa[campo].strip():
            erro("", f"falta o campo de texto '{campo}'.")

    if conversa.get("tema") and conversa["tema"] not in temas:
        erro("", f"o tema '{conversa['tema']}' não existe em temas.json.")
    if conversa.get("cor") and not PADRAO_COR.match(str(conversa["cor"])):
        erro("", "'cor' deve estar no formato #RRGGBB.")
    if "avatar" in conversa and not isinstance(conversa["avatar"], str):
        erro("", "'avatar' deve ser um texto (caminho de arquivo ou link).")

    voz = conversa.get("voz")
    if voz is not None:
        if not isinstance(voz, dict) or not voz.get("nome"):
            erro("", "'voz' precisa ser um objeto com o campo 'nome'.")
        else:
            if not PADRAO_VELOCIDADE.match(str(voz.get("velocidade", "+0%"))):
                erro("", "'velocidade' da voz deve ter o formato '-20%' ou '+10%'.")
            if not PADRAO_TOM.match(str(voz.get("tom", "+0Hz"))):
                erro("", "'tom' da voz deve ter o formato '-10Hz' ou '+5Hz'.")

    humor = conversa.get("humor", {})
    if not isinstance(humor, dict) or any(
        isinstance(valor, bool) or not isinstance(valor, (int, float)) for valor in humor.values()
    ):
        erro("", "'humor' deve ser um objeto com números (ex.: {\"medo\": 20}).")

    variaveis_definidas = conversa.get("variaveis", {})
    if not isinstance(variaveis_definidas, dict):
        erro("", "'variaveis' deve ser um objeto.")
        variaveis_definidas = {}
    variaveis = set(variaveis_definidas) | {"jogador"}

    nos = conversa.get("nos")
    if not isinstance(nos, dict) or not nos:
        erro("", "falta 'nos' (os nós da conversa).")
        return erros, avisos

    inicio = conversa.get("inicio")
    if not isinstance(inicio, str) or inicio not in nos:
        erro("", f"o nó inicial '{inicio}' não existe em 'nos'.")

    pontuacao = conversa.get("pontuacao")
    referenciados = {inicio}
    if pontuacao is not None:
        destinos = pontuacao.get("destinos") if isinstance(pontuacao, dict) else None
        if not isinstance(destinos, dict) or not destinos:
            erro("", "'pontuacao' precisa de 'destinos' (categoria -> nó final).")
            pontuacao = None
        else:
            if pontuacao.get("empate") not in destinos:
                erro("", "'empate' precisa ser uma das categorias de 'destinos'.")
            for categoria, destino in destinos.items():
                if destino not in nos:
                    erro("", f"o destino '{destino}' ({categoria}) não existe em 'nos'.")
                referenciados.add(destino)

    for nome_no, no in nos.items():
        local = f"nó '{nome_no}'"
        if not isinstance(no, dict):
            erro(local, "precisa ser um objeto.")
            continue

        if not no.get("fala") and not no.get("narracao"):
            erro(local, "o nó não tem 'fala' nem 'narracao'.")
        if no.get("tema") and no["tema"] not in temas:
            erro(local, f"o tema '{no['tema']}' não existe em temas.json.")
        if no.get("cor") and not PADRAO_COR.match(str(no["cor"])):
            erro(local, "'cor' deve estar no formato #RRGGBB.")

        opcoes = no.get("opcoes", [])
        if not isinstance(opcoes, list):
            erro(local, "'opcoes' deve ser uma lista.")
            continue
        if len(opcoes) > 25:
            erro(local, "mais de 25 opções.")

        for campo, texto in _textos_do_no(no):
            for variavel in PADRAO_VARIAVEL.findall(texto):
                if variavel not in variaveis:
                    erro(local, f"usa {{{variavel}}} em '{campo}', mas ela não existe em 'variaveis'.")

        for numero, opcao in enumerate(opcoes, start=1):
            onde = f"{local}, opção {numero}"
            if not isinstance(opcao, dict) or not isinstance(opcao.get("texto"), str) or "proximo" not in opcao:
                erro(onde, "precisa de 'texto' e 'proximo'.")
                continue
            if len(opcao["texto"]) > 80:
                erro(onde, "o 'texto' passa de 80 caracteres (limite do botão do Discord).")

            proximo = opcao["proximo"]
            if proximo == RESULTADO:
                if not pontuacao:
                    erro(onde, "usa '@resultado', mas a conversa não tem 'pontuacao'.")
            elif proximo is not None:
                if proximo not in nos:
                    erro(onde, f"aponta para o nó '{proximo}', que não existe.")
                referenciados.add(proximo)

            abordagem = opcao.get("abordagem")
            if abordagem and (not pontuacao or abordagem not in pontuacao["destinos"]):
                erro(onde, f"usa a abordagem '{abordagem}', que não está em 'pontuacao'.")

    orfaos = sorted(set(nos) - referenciados)
    if orfaos:
        avisos.append(f"[{origem}] nós que nenhuma opção alcança: {', '.join(orfaos)}.")

    presos = _nos_sem_saida(nos)
    if presos:
        avisos.append(
            f"[{origem}] nós de onde a conversa nunca consegue terminar (só dá voltas): "
            f"{', '.join(presos)}."
        )
    return erros, avisos


def _nos_sem_saida(nos: dict) -> list:
    """Nós que não levam a nenhum final (nó sem opções, 'proximo': null ou '@resultado')."""

    def opcoes_do(no):
        lista = no.get("opcoes") if isinstance(no, dict) else None
        return [o for o in lista if isinstance(o, dict)] if isinstance(lista, list) else []

    com_saida = {
        nome
        for nome, no in nos.items()
        if isinstance(no, dict)
        and (
            not opcoes_do(no)
            or any(o.get("proximo") is None or o.get("proximo") == RESULTADO for o in opcoes_do(no))
        )
    }
    mudou = True
    while mudou:  # propaga: quem chega a um nó com saída também tem saída
        mudou = False
        for nome, no in nos.items():
            if nome in com_saida or not isinstance(no, dict):
                continue
            if any(isinstance(o.get("proximo"), str) and o["proximo"] in com_saida for o in opcoes_do(no)):
                com_saida.add(nome)
                mudou = True
    return sorted(n for n, no in nos.items() if isinstance(no, dict) and n not in com_saida)


@dataclass
class Catalogo:
    """Tudo o que foi lido de data/: conversas, temas e os problemas encontrados."""

    conversas: dict = field(default_factory=dict)
    temas: dict = field(default_factory=dict)
    erros: list = field(default_factory=list)
    avisos: list = field(default_factory=list)

    @classmethod
    def carregar(cls, pasta_dados) -> "Catalogo":
        pasta_dados = Path(pasta_dados)
        catalogo = cls()
        catalogo.temas = carregar_temas(pasta_dados / "temas.json", catalogo.erros)

        for subpasta, tipo in SUBPASTAS:
            pasta = pasta_dados / subpasta
            if not pasta.is_dir():
                continue
            for arquivo in sorted(pasta.glob("*.json")):
                origem = f"{subpasta}/{arquivo.name}"
                conversa = _ler_json(arquivo, origem, catalogo.erros)
                if conversa is None:
                    continue
                if not isinstance(conversa, dict):
                    catalogo.erros.append(f"[{origem}] o arquivo precisa ser um objeto JSON.")
                    continue

                chave = str(conversa.get("id") or arquivo.stem)
                if chave in catalogo.conversas:
                    catalogo.erros.append(
                        f"[{origem}] o id '{chave}' já é usado por "
                        f"{catalogo.conversas[chave]['_origem']}."
                    )
                    continue

                conversa["id"] = chave
                conversa["tipo"] = tipo
                conversa["_origem"] = origem
                erros, avisos = validar_conversa(chave, conversa, catalogo.temas, origem)
                catalogo.erros.extend(erros)
                catalogo.avisos.extend(avisos)
                catalogo.conversas[chave] = conversa
        return catalogo
