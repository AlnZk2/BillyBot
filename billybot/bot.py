"""
bot.py - A classe BillyBot (o "coração" que junta configurações, dados e cogs).
"""

import logging

import discord
from discord.ext import commands

from billybot.core.carregador import Catalogo
from billybot.config import Settings
from billybot.services.tts import Locutor
from billybot.ui.embeds import FabricaEmbeds

log = logging.getLogger("billybot")


class BillyBot(commands.Bot):
    # Cada cog é um arquivo em billybot/cogs/. Para ligar um sistema novo,
    # crie o arquivo e acrescente o caminho aqui.
    EXTENSOES = (
        "billybot.cogs.dialogos",
        "billybot.cogs.voz",
        "billybot.cogs.erros",
    )

    def __init__(self, settings: Settings, catalogo: Catalogo):
        intents = discord.Intents.default()
        intents.message_content = True  # necessário para ler comandos com "!"
        super().__init__(command_prefix="!", intents=intents)

        self.settings = settings
        self.catalogo = catalogo
        self.embeds = FabricaEmbeds(catalogo.temas)
        self.locutor = Locutor(self, settings.voz_canal_id, settings.ffmpeg_path)
        self.add_check(self._somente_canal_de_comandos)

    async def _somente_canal_de_comandos(self, ctx: commands.Context) -> bool:
        """Se CANAL_COMANDOS_ID for 0, o bot aceita comandos em qualquer canal."""
        canal_id = self.settings.canal_comandos_id
        return canal_id == 0 or ctx.channel.id == canal_id

    async def setup_hook(self) -> None:
        for extensao in self.EXTENSOES:
            await self.load_extension(extensao)
            log.info("Cog carregado: %s", extensao)

    async def on_ready(self) -> None:
        log.info("Bot online como %s (ID: %s)", self.user, self.user.id)
