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

from billybot.core.carregador import hex_para_int
from billybot.core.motor import aplicar_variaveis

TEMA_PADRAO = {"cor": "#8A9199", "icone": "", "nome": ""}


def nome_do(jogador) -> str:
    """Nome usado no lugar de {jogador}. Sem jogador marcado, vira 'viajante'."""
    return jogador.display_name if jogador else "viajante"


def _citar(texto: str) -> str:
    """Põe cada linha da fala em citação do Discord ('> ')."""
    return "\n".join(f"> {linha}" for linha in texto.splitlines() or [texto])


class FabricaEmbeds:
    def __init__(self, temas: dict):
        self.temas = temas  # o !recarregar troca este dicionário

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
