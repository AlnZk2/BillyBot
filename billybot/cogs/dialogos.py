"""
dialogos.py - Comandos de conversa: um comando por arquivo JSON de data/.

    !deuzebio @jogador      atalho criado a partir de data/npcs/deuzebio.json
    !falar deuzebio @jogador  mesma coisa, pelo id
    !conversas              lista tudo o que existe
    !recarregar             relê os JSON sem reiniciar o bot
"""

import logging

import discord
from discord.ext import commands

from billybot.core.carregador import Catalogo
from billybot.services.avatares import localizar_avatar
from billybot.ui.views import DialogoView

log = logging.getLogger("billybot.dialogos")


class Dialogos(commands.Cog):
    """Conversas com NPCs e histórias."""

    def __init__(self, bot):
        self.bot = bot
        self._atalhos = []  # nomes dos comandos criados a partir dos JSON

    async def cog_load(self):
        self._registrar_atalhos()

    async def cog_unload(self):
        self._remover_atalhos()

    # ------------------------------------------------------------------
    # Atalhos dinâmicos: um comando por conversa
    # ------------------------------------------------------------------
    def _criar_atalho(self, chave, conversa):
        async def callback(ctx, jogador: discord.Member = None):
            await self.iniciar(ctx, chave, jogador)

        return commands.Command(
            callback,
            name=chave,
            help=f"{conversa['descricao']} Uso: !{chave} [@jogador]",
        )

    def _registrar_atalhos(self):
        for chave, conversa in self.bot.catalogo.conversas.items():
            if chave in self.bot.all_commands:
                log.warning("O id '%s' já é um comando; use !falar %s.", chave, chave)
                continue
            self.bot.add_command(self._criar_atalho(chave, conversa))
            self._atalhos.append(chave)

    def _remover_atalhos(self):
        for chave in self._atalhos:
            self.bot.remove_command(chave)
        self._atalhos.clear()

    # ------------------------------------------------------------------
    # Publicar a conversa
    # ------------------------------------------------------------------
    async def iniciar(self, ctx, chave, jogador=None):
        bot = self.bot
        conversa = bot.catalogo.conversas[chave]

        # Sem CANAL_RPG_ID, a conversa aparece no mesmo canal do comando.
        canal_id = bot.settings.canal_rpg_id
        canal = bot.get_channel(canal_id) if canal_id else ctx.channel
        if canal is None:
            await ctx.send(embed=bot.embeds.erro(
                "Canal do RPG não encontrado",
                "Confira o `CANAL_RPG_ID` no `.env` e se o bot tem acesso a esse canal.",
            ))
            return

        # O relatório só vai ao mestre se a conversa for publicada em outro canal,
        # senão os jogadores veriam o placar.
        canal_mestre = ctx.channel if canal.id != ctx.channel.id else None

        # Foto de perfil: arquivo local vai anexado à mensagem; link vai direto no embed
        arquivo, avatar_url = localizar_avatar(
            chave, conversa, bot.settings.raiz, bot.settings.pasta_imagens
        )
        extras = {}
        if arquivo:
            nome_anexo = f"avatar{arquivo.suffix.lower()}"
            extras["file"] = discord.File(arquivo, filename=nome_anexo)
            avatar_url = f"attachment://{nome_anexo}"

        view = DialogoView(bot, conversa, jogador, canal_mestre, avatar_url)
        embed = bot.embeds.no_de_conversa(conversa, view.sessao.no, jogador, avatar_url=avatar_url)
        try:
            view.mensagem = await canal.send(embed=embed, view=view, **extras)
        except discord.Forbidden:
            await ctx.send(embed=bot.embeds.erro(
                "Sem permissão",
                "O bot não pode escrever (ou anexar arquivos) no canal do RPG.",
            ))
            return

        await view.abrir_voz()

        if canal_mestre is not None:
            await ctx.send(embed=bot.embeds.sucesso(
                "Conversa publicada", f"**{conversa['npc']}** em {canal.mention}."
            ))

    # ------------------------------------------------------------------
    # Comandos fixos
    # ------------------------------------------------------------------
    @commands.command(name="falar", help="Inicia uma conversa pelo id. Uso: !falar <id> [@jogador]")
    async def falar(self, ctx, chave: str, jogador: discord.Member = None):
        chave = chave.lower()
        if chave not in self.bot.catalogo.conversas:
            await ctx.send(embed=self.bot.embeds.erro(
                "Conversa não encontrada", f"Não existe `{chave}`. Use `!conversas` para ver a lista."
            ))
            return
        await self.iniciar(ctx, chave, jogador)

    @commands.command(name="conversas", help="Lista as conversas disponíveis.")
    async def conversas(self, ctx):
        await ctx.send(embed=self.bot.embeds.lista_de_conversas(self.bot.catalogo.conversas))

    @commands.command(name="recarregar", help="Relê os arquivos JSON de data/ sem reiniciar o bot.")
    async def recarregar(self, ctx):
        novo = Catalogo.carregar(self.bot.settings.pasta_dados)
        if novo.erros:
            linhas = [f"• {erro[:300]}" for erro in novo.erros[:10]]
            if len(novo.erros) > 10:
                linhas.append(f"… e mais {len(novo.erros) - 10} erro(s).")
            await ctx.send(embed=self.bot.embeds.erro(
                "Nada foi recarregado", "\n".join(linhas) + "\n\nCorrija o JSON e tente de novo."
            ))
            return

        self._remover_atalhos()
        self.bot.catalogo = novo
        self.bot.embeds.temas = novo.temas
        self._registrar_atalhos()
        await ctx.send(embed=self.bot.embeds.sucesso(
            "Dados recarregados",
            f"{len(novo.conversas)} conversas e {len(novo.temas)} temas carregados.",
        ))


async def setup(bot):
    await bot.add_cog(Dialogos(bot))
