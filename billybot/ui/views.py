"""
views.py - Botões de resposta e controle da conversa (a "roda de diálogo").
"""

import discord

from billybot.core.motor import Sessao, aplicar_variaveis
from billybot.ui.embeds import nome_do


class BotaoOpcao(discord.ui.Button):
    def __init__(self, texto, indice, posicao):
        super().__init__(
            label=texto[:80],
            style=discord.ButtonStyle.secondary,
            row=posicao // 5,  # até 5 botões por linha
        )
        self.indice = indice  # posição da opção dentro do nó

    async def callback(self, interaction: discord.Interaction):
        await self.view.escolher(interaction, self.indice)


class DialogoView(discord.ui.View):
    def __init__(self, bot, conversa, jogador, canal_mestre=None, avatar_url=None):
        super().__init__(timeout=bot.settings.tempo_limite)
        self.bot = bot
        self.conversa = conversa
        self.jogador = jogador            # None = qualquer pessoa pode responder
        self.canal_mestre = canal_mestre  # recebe o relatório ao fim (ou None)
        self.avatar_url = avatar_url
        self.voz = conversa.get("voz")    # None = este NPC não fala
        self.voz_aberta = False
        self.sessao = Sessao(conversa)
        self.mensagem = None
        self._montar_botoes()

    def _embed(self, encerrada=False, reacao=None):
        return self.bot.embeds.no_de_conversa(
            self.conversa,
            self.sessao.no,
            self.jogador,
            reacao=reacao,
            encerrada=encerrada,
            avatar_url=self.avatar_url,
        )

    def _montar_botoes(self):
        self.clear_items()
        nome = nome_do(self.jogador)
        for posicao, (indice, opcao) in enumerate(self.sessao.opcoes_visiveis()):
            texto = aplicar_variaveis(opcao["texto"], self.conversa, nome)
            self.add_item(BotaoOpcao(texto, indice, posicao))

    # ---- voz (TTS): só a "fala" é falada, nunca a narração ----
    def _usa_voz(self):
        return bool(self.voz) and self.bot.locutor.ligado

    def _texto_falado(self):
        no = self.sessao.no
        texto = no.get("fala_tts") or no.get("fala") or ""
        return aplicar_variaveis(
            texto, self.conversa, nome_do(self.jogador), para_voz=True
        ).strip()

    async def abrir_voz(self):
        """Chamado quando a conversa é publicada: entra no canal e fala a 1ª carta."""
        if not self._usa_voz():
            return
        self.voz_aberta = True
        self.bot.locutor.abrir()
        self._falar_agora()

    def _falar_agora(self):
        texto = self._texto_falado()
        if self.voz_aberta and texto:
            self.bot.locutor.falar_em_segundo_plano(texto, self.voz)

    def _fechar_voz(self):
        if self.voz_aberta:
            self.voz_aberta = False
            self.bot.locutor.fechar()

    # ---- interação ----
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Com jogador marcado, só ele clica. Sem marcar, qualquer um pode."""
        if self.jogador and interaction.user.id != self.jogador.id:
            await interaction.response.send_message(
                "Essa conversa não é sua.", ephemeral=True
            )
            return False
        return True

    async def escolher(self, interaction: discord.Interaction, indice):
        passos_antes = len(self.sessao.caminho)
        continua = self.sessao.escolher(indice)
        embed = self._embed(encerrada=not continua, reacao=self.sessao.reacao)

        if continua:
            self._montar_botoes()
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=None)

        # Só fala se mudou de carta (clicar em "Encerrar" não repete a fala)
        if len(self.sessao.caminho) > passos_antes:
            self._falar_agora()

        if not continua:
            await self._avisar_mestre("terminou")
            self._fechar_voz()
            self.stop()

    async def _avisar_mestre(self, motivo):
        """Relatório privado no canal de comandos (só se for outro canal)."""
        if self.canal_mestre is None:
            return
        texto = (
            f"Conversa **{self.conversa['npc']}** com **{nome_do(self.jogador)}** "
            f"{motivo}.\n{self.sessao.resumo()}"
        )
        try:
            await self.canal_mestre.send(texto)
        except discord.HTTPException:
            pass

    async def on_timeout(self):
        if self.mensagem is None:
            return
        try:
            await self.mensagem.edit(embed=self._embed(encerrada=True), view=None)
        except discord.HTTPException:
            pass
        await self._avisar_mestre("expirou por falta de resposta")
        self._fechar_voz()
