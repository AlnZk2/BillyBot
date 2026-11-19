"""
embeds.py - Todos os embeds do bot saem daqui (item 2).

A FabricaEmbeds usa os temas de data/temas.json. Cada conversa (e cada nó)
pode escolher um tema, e a cor, o ícone e o nome do ambiente mudam sozinhos:

    criogenia  azul estéril, laboratório criogênico
    alerta     vermelho, radiação, fungos e perigo
    seguro     verde, áreas seguras
    info / sucesso / erro   mensagens do próprio bot

Formatação: narração em itálico, fala do NPC em citação (>), e no rodapé o
ambiente atual. O TTS lê apenas o texto da citação.
"""

from __future__ import annotations

import discord

from billybot.core.carregador import CATEGORIAS_DE_ITENS, hex_para_int
from billybot.core.motor import aplicar_variaveis

TEMA_PADRAO = {"cor": "#8A9199", "icone": "", "nome": ""}


def nome_do(jogador) -> str:
    """Nome usado no lugar de {jogador}. Sem jogador marcado, vira 'viajante'."""
    return jogador.display_name if jogador else "viajante"


def barra(atual: int, maximo: int, tamanho: int = 10) -> str:
    """Barra de saúde em texto: ▰▰▰▰▰▱▱▱▱▱"""
    if not maximo:
        return "▱" * tamanho  # sem saúde máxima definida, mostra a barra vazia
    cheios = round(tamanho * atual / maximo)
    if atual > 0 and cheios == 0:
        cheios = 1  # com vida sobrando, nunca mostra a barra totalmente vazia
    cheios = max(0, min(tamanho, cheios))
    return "▰" * cheios + "▱" * (tamanho - cheios)


def _citar(texto: str) -> str:
    """Põe cada linha da fala em citação do Discord ('> ')."""
    return "\n".join(f"> {linha}" for linha in texto.splitlines() or [texto])


class FabricaEmbeds:
    def __init__(self, temas: dict, itens: dict | None = None):
        self.temas = temas  # o !recarregar troca estes dicionários
        self.itens = itens or {}

    def tema(self, chave: str | None) -> dict:
        return self.temas.get(chave or "padrao") or self.temas.get("padrao") or TEMA_PADRAO

    def resolver_visual(self, conversa: dict, no: dict) -> tuple[int, str]:
        """Cor e etiqueta do ambiente de um nó.

        Precedência da cor: 'cor' do nó > tema do nó > 'cor' da conversa > tema da conversa.
        """
        tema_do_no = no.get("tema")
        tema = self.tema(tema_do_no or conversa.get("tema"))
        cor = no.get("cor") or (None if tema_do_no else conversa.get("cor")) or tema["cor"]
        etiqueta = f"{tema.get('icone', '')} {tema.get('nome', '')}".strip()
        return hex_para_int(cor), etiqueta

    # ------------------------------------------------------------------
    # Conversas
    # ------------------------------------------------------------------
    def no_de_conversa(
        self, conversa, no, jogador, reacao=None, encerrada=False, avatar_url=None
    ) -> discord.Embed:
        nome = nome_do(jogador)

        def v(texto):
            return aplicar_variaveis(texto, conversa, nome)

        partes = []
        # Narração (itálico): a reação à resposta anterior + a cena do nó.
        narracao = " ".join(t for t in (reacao, no.get("narracao")) if t)
        if narracao:
            partes.append(f"*{v(narracao)}*")
        # Fala do NPC (citação): é só isto que o TTS lê.
        if no.get("fala"):
            partes.append(_citar(v(no["fala"])))
        if no.get("narracao_final"):
            partes.append(f"*{v(no['narracao_final'])}*")

        cor, etiqueta = self.resolver_visual(conversa, no)
        embed = discord.Embed(
            title=None if avatar_url else conversa["npc"],
            description="\n\n".join(partes) or "...",
            color=cor,
        )
        if avatar_url:
            # Foto de perfil redonda ao lado do nome, como num chat
            embed.set_author(name=conversa["npc"], icon_url=avatar_url)
        if conversa.get("imagem"):
            embed.set_thumbnail(url=conversa["imagem"])
        if no.get("itens"):
            embed.add_field(
                name="Itens obtidos",
                value="\n".join(f"• {v(item)}" for item in no["itens"]),
                inline=False,
            )

        rodape = [etiqueta] if etiqueta else []
        rodape.append(f"Conversa com {jogador.display_name}" if jogador else "Conversa aberta a todos")
        if encerrada:
            rodape.append("Conversa encerrada")
        embed.set_footer(text=" • ".join(rodape))
        return embed

    # ------------------------------------------------------------------
    # Mensagens do próprio bot
    # ------------------------------------------------------------------
    def _simples(self, chave_tema: str, titulo: str, texto: str | None) -> discord.Embed:
        tema = self.tema(chave_tema)
        icone = tema.get("icone", "")
        return discord.Embed(
            title=f"{icone} {titulo}".strip(),
            description=texto,
            color=hex_para_int(tema["cor"]),
        )

    def info(self, titulo: str, texto: str | None = None) -> discord.Embed:
        return self._simples("info", titulo, texto)

    def sucesso(self, titulo: str, texto: str | None = None) -> discord.Embed:
        return self._simples("sucesso", titulo, texto)

    def erro(self, titulo: str, texto: str | None = None) -> discord.Embed:
        return self._simples("erro", titulo, texto)

    def lista_de_conversas(self, conversas: dict) -> discord.Embed:
        grupos = {"npc": [], "historia": []}
        for chave, conversa in conversas.items():
            linha = f"`!{chave} [@jogador]` — {conversa['descricao']}"
            grupos.setdefault(conversa.get("tipo", "npc"), []).append(linha)

        partes = []
        if grupos["npc"]:
            partes.append("**NPCs**\n" + "\n".join(grupos["npc"]))
        if grupos["historia"]:
            partes.append("**História**\n" + "\n".join(grupos["historia"]))
        texto = "\n\n".join(partes) or "Nenhuma conversa encontrada na pasta `data/`."
        if len(texto) > 4000:  # limite do Discord é 4096
            texto = texto[:3990] + "\n…"
        return self.info("Conversas disponíveis", texto)

    # ------------------------------------------------------------------
    # Ficha, inventário e memória (itens 3 e 4)
    # ------------------------------------------------------------------
    def texto_do_inventario(self, inventario: dict) -> str:
        if not inventario:
            return "*Vazio*"
        grupos: dict = {}
        for item_id, quantidade in sorted(inventario.items()):
            item = self.itens.get(item_id, {"nome": item_id, "categoria": "diverso"})
            emoji = item.get("emoji") or CATEGORIAS_DE_ITENS.get(item.get("categoria", "diverso"), ("▫️",))[0]
            grupos.setdefault(item.get("categoria", "diverso"), []).append(
                f"{emoji} {item['nome']} ×{quantidade}"
            )
        blocos = [
            f"**{titulo}**\n" + "\n".join(grupos[categoria])
            for categoria, (_, titulo) in CATEGORIAS_DE_ITENS.items()
            if categoria in grupos
        ]
        texto = "\n\n".join(blocos)
        return texto if len(texto) <= 1000 else texto[:990] + "\n…"

    def ficha(self, personagem: dict, inventario: dict, usuario=None, marcas: list | None = None):
        """Ficha do personagem. A cor segue a saúde: verde, âmbar ou vermelho."""
        atual, maximo = personagem["saude"], personagem["saude_max"]
        razao = atual / maximo if maximo else 0
        tema = self.tema("seguro" if razao >= 0.6 else "aviso" if razao >= 0.3 else "alerta")

        embed = discord.Embed(
            title=f"{tema.get('icone', '')} Ficha de {personagem['personagem']}".strip(),
            color=hex_para_int(tema["cor"]),
        )
        embed.add_field(name="Saúde", value=f"{barra(atual, maximo)}  {atual}/{maximo}", inline=False)
        embed.add_field(name="Status", value=personagem["status"], inline=True)
        embed.add_field(name="Local", value=personagem["local"], inline=True)
        embed.add_field(name="Inventário", value=self.texto_do_inventario(inventario), inline=False)
        if marcas is not None:  # só o mestre vê as marcas
            texto = "\n".join(f"• `{m['marca']}`" for m in marcas) or "*Nenhuma*"
            embed.add_field(name="Escolhas marcantes", value=texto[:1000], inline=False)

        avatar = getattr(getattr(usuario, "display_avatar", None), "url", None)
        if avatar:
            embed.set_thumbnail(url=avatar)
        embed.set_footer(text="Subsolo 57 • Ficha de sobrevivente")
        return embed

    def memoria(self, jogador, resumo: list, marcas: list) -> discord.Embed:
        linhas = [
            f"`{r['conversa']}`: {r['execucoes']} vez(es), {r['cartas']} carta(s) vista(s), "
            f"último final: {r['ultimo_final'] or 'sem final'}"
            for r in resumo
        ]
        embed = self.info(f"Memória de {jogador.display_name}")
        embed.add_field(name="Conversas", value="\n".join(linhas)[:1000] or "*Nenhuma conversa registrada*", inline=False)
        embed.add_field(
            name="Marcas",
            value="\n".join(f"• `{m['marca']}` ({m['conversa']}, {m['quando'][:10]})" for m in marcas)[:1000]
            or "*Nenhuma*",
            inline=False,
        )
        return embed

    def lista_de_itens(self) -> discord.Embed:
        grupos: dict = {}
        for item_id, item in self.itens.items():
            emoji = item.get("emoji") or CATEGORIAS_DE_ITENS[item.get("categoria", "diverso")][0]
            grupos.setdefault(item.get("categoria", "diverso"), []).append(f"`{item_id}` — {emoji} {item['nome']}")
        blocos = [
            f"**{titulo}**\n" + "\n".join(grupos[categoria])
            for categoria, (_, titulo) in CATEGORIAS_DE_ITENS.items()
            if categoria in grupos
        ]
        texto = "\n\n".join(blocos) or "Nenhum item cadastrado em `data/itens.json`."
        if len(texto) > 4000:
            texto = texto[:3990] + "\n…"
        return self.info("Itens cadastrados", texto)
