"""
memoria.py - Ferramentas do mestre para a memória de escolhas (item 4).

    !memoria @jogador                       histórico e marcas do jogador
    !marca @jogador <marca>                 dá uma marca à mão
    !desmarcar @jogador <marca>             tira uma marca
    !esquecer @jogador [conversa] confirmar apaga a memória
"""

import discord
from discord.ext import commands

from billybot.core.carregador import PADRAO_ID


class MemoriaDeEscolhas(commands.Cog, name="Memoria"):
    """Memória de escolhas dos jogadores."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="memoria", help="Mostra o histórico e as marcas de um jogador. Uso: !memoria @jogador")
    async def memoria(self, ctx, jogador: discord.Member):
        resumo = await self.bot.memoria.resumo(jogador.id)
        marcas = await self.bot.memoria.marcas(jogador.id)
        await ctx.send(embed=self.bot.embeds.memoria(jogador, resumo, marcas))

    @commands.command(name="marca", help="Dá uma marca ao jogador. Uso: !marca @jogador <marca>")
    async def marca(self, ctx, jogador: discord.Member, marca: str):
        marca = marca.lower()
        if not PADRAO_ID.match(marca):
            await ctx.send(embed=self.bot.embeds.erro(
                "Marca inválida", "Use só letras minúsculas, números e _ (sem espaços ou acentos)."
            ))
            return
        nova = await self.bot.memoria.adicionar_marca(jogador.id, marca)
        titulo, texto = (
            ("Marca adicionada", f"`{marca}` agora vale para {jogador.display_name}.")
            if nova else ("Já tinha a marca", f"{jogador.display_name} já tem `{marca}`.")
        )
        await ctx.send(embed=self.bot.embeds.sucesso(titulo, texto))

    @commands.command(name="desmarcar", help="Tira uma marca do jogador. Uso: !desmarcar @jogador <marca>")
    async def desmarcar(self, ctx, jogador: discord.Member, marca: str):
        removida = await self.bot.memoria.remover_marca(jogador.id, marca.lower())
        if removida:
            await ctx.send(embed=self.bot.embeds.sucesso(
                "Marca removida", f"`{marca.lower()}` saiu de {jogador.display_name}."
            ))
        else:
            await ctx.send(embed=self.bot.embeds.erro(
                "Marca não encontrada", f"{jogador.display_name} não tem `{marca.lower()}`."
            ))

    @commands.command(
        name="esquecer",
        help="Apaga a memória de um jogador. Uso: !esquecer @jogador [conversa] confirmar",
    )
    async def esquecer(self, ctx, jogador: discord.Member, conversa: str = None, confirmar: str = None):
        if conversa == "confirmar":  # !esquecer @jogador confirmar  (apaga tudo)
            conversa, confirmar = None, "confirmar"
        alvo = f"da conversa `{conversa}`" if conversa else "de **todas** as conversas"
        if confirmar != "confirmar":
            await ctx.send(embed=self.bot.embeds.info(
                "Confirme para apagar",
                f"Isto apaga a memória {alvo} de {jogador.display_name} (visitas, escolhas e marcas). "
                "Repita o comando terminando com `confirmar`.",
            ))
            return
        apagado = await self.bot.memoria.esquecer(jogador.id, conversa.lower() if conversa else None)
        await ctx.send(embed=self.bot.embeds.sucesso(
            "Memória apagada",
            f"{apagado['execucoes']} conversa(s) e {apagado['marcas']} marca(s) removidas de {jogador.display_name}.",
        ))


async def setup(bot):
    await bot.add_cog(MemoriaDeEscolhas(bot))
