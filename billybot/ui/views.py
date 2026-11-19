"""
views.py - Botões de resposta e controle da conversa (a "roda de diálogo").
"""

import logging

import discord

from billybot.core.motor import Sessao, aplicar_variaveis
from billybot.services.personagens import PersonagemInexistente
from billybot.ui.embeds import nome_do

log = logging.getLogger("billybot.views")


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
    def __init__(
        self, bot, conversa, jogador, canal_mestre=None, avatar_url=None,
        contexto=None, execucao_id=None,
    ):
        super().__init__(timeout=bot.settings.tempo_limite)
        self.bot = bot
        self.conversa = conversa
        self.jogador = jogador            # None = qualquer pessoa pode responder
        self.canal_mestre = canal_mestre  # recebe o relatório ao fim (ou None)
        self.avatar_url = avatar_url
        self.voz = conversa.get("voz")    # None = este NPC não fala
        self.voz_aberta = False
        self.execucao_id = execucao_id    # None = esta conversa não é gravada na memória
        self.memoria_fechada = False
        self.sessao = Sessao(conversa, contexto)
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

    # ---- memória (item 4): grava visitas, escolhas, marcas e itens ----
    def _memoria_ativa(self):
        return self.jogador is not None and self.execucao_id is not None

    async def abrir_memoria(self):
        """Chamado quando a conversa é publicada: grava a primeira carta."""
        await self._persistir()

    async def _persistir(self):
        eventos = self.sessao.drenar_eventos()
        if not eventos or not self._memoria_ativa():
            return
        bot, jogador_id = self.bot, self.jogador.id
        try:
            await bot.memoria.registrar(
                self.execucao_id, jogador_id, self.conversa.get("id", "?"), eventos
            )
        except Exception:
            log.exception("Não consegui gravar a memória da conversa.")

        for evento in eventos:
            if evento[0] != "itens":
                continue
            try:
                await bot.personagens.dar_itens(jogador_id, evento[1])
            except PersonagemInexistente:
                lista = ", ".join(f"{item} x{qtd}" for item, qtd in evento[1].items())
                await self._enviar_ao_mestre(
                    f"**{nome_do(self.jogador)}** ainda não tem personagem: itens não entregues "
                    f"({lista}). Use `!personagem @jogador <nome>` e `!dar`."
                )
            except Exception:
                log.exception("Não consegui entregar os itens ao jogador.")

    async def _finalizar_memoria(self, motivo):
        if self.memoria_fechada or not self._memoria_ativa():
            return
        self.memoria_fechada = True
        try:
            await self.bot.memoria.finalizar_execucao(
                self.execucao_id, self.sessao.no_atual, motivo
            )
        except Exception:
            log.exception("Não consegui finalizar o registro da conversa.")

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

        await self._persistir()

        if not continua:
            await self._avisar_mestre("terminou")
            await self._finalizar_memoria("terminou")
            self._fechar_voz()
            self.stop()

    async def _enviar_ao_mestre(self, texto):
        """Mensagem privada no canal de comandos (só se for outro canal)."""
        if self.canal_mestre is None:
            return
        try:
            await self.canal_mestre.send(texto)
        except discord.HTTPException:
            pass

    async def _avisar_mestre(self, motivo):
        await self._enviar_ao_mestre(
            f"Conversa **{self.conversa['npc']}** com **{nome_do(self.jogador)}** "
            f"{motivo}.\n{self.sessao.resumo()}"
        )

    async def on_timeout(self):
        if self.mensagem is None:
            return
        try:
            await self.mensagem.edit(embed=self._embed(encerrada=True), view=None)
        except discord.HTTPException:
            pass
        await self._avisar_mestre("expirou por falta de resposta")
        await self._finalizar_memoria("expirou")
        self._fechar_voz()
