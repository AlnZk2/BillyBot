"""
erros.py - Respostas amigáveis para os erros mais comuns de comando.
"""

import traceback

from discord.ext import commands


class Erros(commands.Cog):
    """Tratamento de erros dos comandos."""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        embeds = self.bot.embeds

        if isinstance(error, commands.CommandNotFound):
            return  # ignora mensagens que começam com "!" mas não são comandos

        if isinstance(error, commands.CheckFailure):
            canal = self.bot.get_channel(self.bot.settings.canal_comandos_id)
            destino = canal.mention if canal else "o canal de comandos"
            await ctx.send(
                embed=embeds.erro("Canal errado", f"{ctx.author.mention}, use {destino}."),
                delete_after=8,
            )
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(
                embed=embeds.erro(
                    "Jogador não encontrado",
                    "Marque o jogador com @ ou deixe sem marcar para liberar a conversa a todos.",
                ),
                delete_after=10,
            )
            return

        if isinstance(error, commands.MissingRequiredArgument):
            uso = f"!{ctx.command.qualified_name} {ctx.command.signature}".strip()
            await ctx.send(
                embed=embeds.erro("Faltou um argumento", f"Uso: `{uso}`"),
                delete_after=10,
            )
            return

        # Erro inesperado: mostra no terminal e avisa o mestre
        traceback.print_exception(type(error), error, error.__traceback__)
        await ctx.send(embed=embeds.erro(
            "Algo deu errado", "O erro foi registrado no terminal do bot."
        ))


async def setup(bot):
    await bot.add_cog(Erros(bot))
