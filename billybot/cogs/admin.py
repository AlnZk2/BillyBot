"""
admin.py - Ferramentas de administração do bot.

    !sincronizar     envia os comandos slash (/sheet) ao Discord
"""

import discord
from discord.ext import commands


class Admin(commands.Cog):
    """Administração."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sincronizar", help="Envia os comandos slash (/sheet) ao Discord.")
    async def sincronizar(self, ctx):
        try:
            comandos, onde = await self.bot.sincronizar_slash()
        except discord.HTTPException as erro:
            await ctx.send(embed=self.bot.embeds.erro("Não consegui sincronizar", str(erro)))
            return
        lista = ", ".join(f"/{comando.name}" for comando in comandos) or "nenhum"
        await ctx.send(embed=self.bot.embeds.sucesso(
            "Comandos slash sincronizados", f"{len(comandos)} comando(s) {onde}: {lista}."
        ))


async def setup(bot):
    await bot.add_cog(Admin(bot))
