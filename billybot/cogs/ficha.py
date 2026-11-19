"""
ficha.py - Ficha de personagem e inventário (item 3).

Para o jogador (comando slash, resposta só para ele):
    /sheet

Para o mestre (no canal de comandos):
    !personagem @jogador <nome>      cria ou renomeia o personagem
    !ficha @jogador                  vê a ficha, com as marcas
    !saude @jogador +10 | -5 | =80   cura, fere ou define a saúde
    !status @jogador <texto>         muda o status (ex.: Contaminado)
    !local @jogador <texto>          muda o local atual
    !dar @jogador <item> [qtd]       entrega itens
    !tirar @jogador <item> [qtd]     retira itens
    !itens                           lista os itens cadastrados
"""

import discord
from discord import app_commands
from discord.ext import commands

from billybot.services.personagens import (
    ItemInsuficiente,
    PersonagemInexistente,
    interpretar_saude,
)
from billybot.ui.embeds import barra


class Ficha(commands.Cog):
    """Ficha de personagem e inventário."""

    def __init__(self, bot):
        self.bot = bot

    def _sem_personagem(self, jogador):
        return self.bot.embeds.erro(
            "Sem personagem",
            f"**{jogador.display_name}** ainda não tem personagem. "
            "Use `!personagem @jogador <nome>`.",
        )

    # ------------------------------------------------------------------
    # Jogador
    # ------------------------------------------------------------------
    @app_commands.command(name="sheet", description="Mostra a sua ficha de sobrevivente e o seu inventário.")
    async def sheet(self, interaction: discord.Interaction):
        bot = self.bot
        dados = await bot.personagens.obter(interaction.user.id)
        if dados is None:
            await interaction.response.send_message(
                embed=bot.embeds.erro(
                    "Você ainda não tem personagem", "Peça ao mestre para criar o seu personagem."
                ),
                ephemeral=True,  # só o próprio jogador vê
            )
            return
        inventario = await bot.personagens.inventario(interaction.user.id)
        await interaction.response.send_message(
            embed=bot.embeds.ficha(dados, inventario, interaction.user), ephemeral=True
        )

    # ------------------------------------------------------------------
    # Mestre
    # ------------------------------------------------------------------
    @commands.command(name="personagem", help="Cria ou renomeia o personagem. Uso: !personagem @jogador <nome>")
    async def personagem(self, ctx, jogador: discord.Member, *, nome: str):
        if len(nome) > 60:
            await ctx.send(embed=self.bot.embeds.erro("Nome muito grande", "Use até 60 caracteres."))
            return
        dados = await self.bot.personagens.criar(jogador.id, nome)
        await ctx.send(embed=self.bot.embeds.sucesso(
            "Personagem salvo", f"**{dados['personagem']}** é o personagem de {jogador.display_name}."
        ))

    @commands.command(name="ficha", help="Mostra a ficha de um jogador. Uso: !ficha @jogador")
    async def ficha(self, ctx, jogador: discord.Member):
        bot = self.bot
        dados = await bot.personagens.obter(jogador.id)
        if dados is None:
            await ctx.send(embed=self._sem_personagem(jogador))
            return
        inventario = await bot.personagens.inventario(jogador.id)
        marcas = await bot.memoria.marcas(jogador.id)
        await ctx.send(embed=bot.embeds.ficha(dados, inventario, jogador, marcas=marcas))

    @commands.command(name="saude", help="Muda a saúde. Uso: !saude @jogador +10 | -5 | =80")
    async def saude(self, ctx, jogador: discord.Member, valor: str):
        bot = self.bot
        try:
            modo, numero = interpretar_saude(valor)
        except ValueError as erro:
            await ctx.send(embed=bot.embeds.erro("Valor inválido", str(erro)))
            return
        try:
            nova = await bot.personagens.ajustar_saude(jogador.id, modo, numero)
        except PersonagemInexistente:
            await ctx.send(embed=self._sem_personagem(jogador))
            return
        dados = await bot.personagens.obter(jogador.id)
        await ctx.send(embed=bot.embeds.sucesso(
            "Saúde atualizada",
            f"**{dados['personagem']}**: {barra(nova, dados['saude_max'])}  {nova}/{dados['saude_max']}",
        ))

    async def _atualizar_texto(self, ctx, jogador, campo, texto):
        bot = self.bot
        if len(texto) > 100:
            await ctx.send(embed=bot.embeds.erro("Texto muito grande", "Use até 100 caracteres."))
            return
        try:
            if campo == "status":
                await bot.personagens.definir_status(jogador.id, texto)
            else:
                await bot.personagens.definir_local(jogador.id, texto)
        except PersonagemInexistente:
            await ctx.send(embed=self._sem_personagem(jogador))
            return
        await ctx.send(embed=bot.embeds.sucesso(
            f"{campo.capitalize()} atualizado", f"{jogador.display_name}: **{texto}**"
        ))

    @commands.command(name="status", help="Muda o status do personagem. Uso: !status @jogador <texto>")
    async def status(self, ctx, jogador: discord.Member, *, texto: str):
        await self._atualizar_texto(ctx, jogador, "status", texto)

    @commands.command(name="local", help="Muda o local do personagem. Uso: !local @jogador <texto>")
    async def local(self, ctx, jogador: discord.Member, *, texto: str):
        await self._atualizar_texto(ctx, jogador, "local", texto)

    @commands.command(name="dar", help="Entrega itens. Uso: !dar @jogador <id_do_item> [quantidade]")
    async def dar(self, ctx, jogador: discord.Member, item: str, quantidade: int = 1):
        bot = self.bot
        item = item.lower()
        if item not in bot.catalogo.itens:
            await ctx.send(embed=bot.embeds.erro(
                "Item desconhecido", f"Não existe `{item}`. Use `!itens` para ver a lista."
            ))
            return
        if quantidade < 1:
            await ctx.send(embed=bot.embeds.erro("Quantidade inválida", "Use um número maior que 0."))
            return
        try:
            total = await bot.personagens.dar_item(jogador.id, item, quantidade)
        except PersonagemInexistente:
            await ctx.send(embed=self._sem_personagem(jogador))
            return
        await ctx.send(embed=bot.embeds.sucesso(
            "Item entregue",
            f"{quantidade}× **{bot.catalogo.itens[item]['nome']}** para {jogador.display_name} "
            f"(agora tem {total}).",
        ))

    @commands.command(name="tirar", help="Retira itens. Uso: !tirar @jogador <id_do_item> [quantidade]")
    async def tirar(self, ctx, jogador: discord.Member, item: str, quantidade: int = 1):
        bot = self.bot
        item = item.lower()
        if quantidade < 1:
            await ctx.send(embed=bot.embeds.erro("Quantidade inválida", "Use um número maior que 0."))
            return
        try:
            sobra = await bot.personagens.tirar_item(jogador.id, item, quantidade)
        except PersonagemInexistente:
            await ctx.send(embed=self._sem_personagem(jogador))
            return
        except ItemInsuficiente as erro:
            await ctx.send(embed=bot.embeds.erro("Não tem o suficiente", f"`{item}`: {erro}."))
            return
        nome = bot.catalogo.itens.get(item, {}).get("nome", item)
        await ctx.send(embed=bot.embeds.sucesso(
            "Item retirado", f"{quantidade}× **{nome}** de {jogador.display_name} (sobraram {sobra})."
        ))

    @commands.command(name="itens", help="Lista os itens cadastrados em data/itens.json.")
    async def itens(self, ctx):
        await ctx.send(embed=self.bot.embeds.lista_de_itens())


async def setup(bot):
    await bot.add_cog(Ficha(bot))
