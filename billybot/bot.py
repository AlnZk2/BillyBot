"""
bot.py - A classe BillyBot (o "coração" que junta configurações, dados e cogs).
"""

import logging

import discord
from discord.ext import commands

from billybot.core.carregador import Catalogo
from billybot.config import Settings
from billybot.services.banco import Banco
from billybot.services.memoria import Memoria
from billybot.services.personagens import Personagens
from billybot.services.tts import Locutor
from billybot.ui.embeds import FabricaEmbeds

log = logging.getLogger("billybot")


class BillyBot(commands.Bot):
    # Cada cog é um arquivo em billybot/cogs/. Para ligar um sistema novo,
    # crie o arquivo e acrescente o caminho aqui.
    EXTENSOES = (
        "billybot.cogs.dialogos",
        "billybot.cogs.ficha",
        "billybot.cogs.memoria",
        "billybot.cogs.voz",
        "billybot.cogs.admin",
        "billybot.cogs.erros",
    )

    def __init__(self, settings: Settings, catalogo: Catalogo):
        intents = discord.Intents.default()
        intents.message_content = True  # necessário para ler comandos com "!"
        super().__init__(command_prefix="!", intents=intents)

        self.settings = settings
        self.catalogo = catalogo
        self.embeds = FabricaEmbeds(catalogo.temas, catalogo.itens)
        self.banco = Banco(settings.caminho_db)
        self.personagens = Personagens(self.banco)
        self.memoria = Memoria(self.banco)
        self.locutor = Locutor(self, settings.voz_canal_id, settings.ffmpeg_path)
        self.add_check(self._somente_canal_de_comandos)

    async def _somente_canal_de_comandos(self, ctx: commands.Context) -> bool:
        """Se CANAL_COMANDOS_ID for 0, o bot aceita comandos em qualquer canal."""
        canal_id = self.settings.canal_comandos_id
        return canal_id == 0 or ctx.channel.id == canal_id

    async def sincronizar_slash(self):
        """Envia os comandos slash (/sheet) ao Discord. Retorna (comandos, onde)."""
        if self.settings.guild_id:
            servidor = discord.Object(id=self.settings.guild_id)
            self.tree.copy_global_to(guild=servidor)
            return await self.tree.sync(guild=servidor), "no servidor configurado (aparecem na hora)"
        return await self.tree.sync(), "globalmente (pode levar até 1 hora para aparecer)"

    async def setup_hook(self) -> None:
        versao = await self.banco.iniciar()
        log.info("Banco de dados pronto (versão %s): %s", versao, self.settings.caminho_db)

        for extensao in self.EXTENSOES:
            await self.load_extension(extensao)
            log.info("Cog carregado: %s", extensao)

        if self.settings.guild_id:  # com GUILD_ID, os slash já nascem sincronizados
            try:
                comandos, onde = await self.sincronizar_slash()
                log.info("%d comando(s) slash sincronizados %s", len(comandos), onde)
            except discord.HTTPException as erro:
                log.warning("Não consegui sincronizar os comandos slash: %s", erro)

    async def on_ready(self) -> None:
        log.info("Bot online como %s (ID: %s)", self.user, self.user.id)
