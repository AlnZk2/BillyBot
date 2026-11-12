"""
voz.py - Ferramentas de voz (TTS) para o mestre.

    !vozes               lista as vozes disponíveis em português do Brasil
    !testarvoz <id>      fala a primeira fala de um NPC no canal de voz
"""

from discord.ext import commands

from billybot.core.motor import aplicar_variaveis
from billybot.services.tts import listar_vozes


class Voz(commands.Cog):
    """Voz dos NPCs."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="vozes", help="Lista as vozes TTS em português do Brasil.")
    async def vozes(self, ctx):
        try:
            vozes = await listar_vozes("pt-BR")
        except Exception as erro:
            await ctx.send(embed=self.bot.embeds.erro("Não consegui listar as vozes", str(erro)))
            return
        linhas = [f"`{v['ShortName']}` ({v['Gender']})" for v in vozes]
        await ctx.send(embed=self.bot.embeds.info(
            "Vozes disponíveis",
            "Use o nome no campo `voz.nome` do JSON:\n" + "\n".join(linhas),
        ))

    @commands.command(
        name="testarvoz",
        help="Testa a voz de um NPC no canal de voz. Uso: !testarvoz <id>",
    )
    async def testarvoz(self, ctx, chave: str = None):
        embeds, locutor = self.bot.embeds, self.bot.locutor
        if not locutor.ligado:
            await ctx.send(embed=embeds.erro(
                "Voz desligada", "Defina o `VOZ_CANAL_ID` no `.env` para ligar."
            ))
            return
        conversa = self.bot.catalogo.conversas.get((chave or "").lower())
        if conversa is None or not conversa.get("voz"):
            await ctx.send(embed=embeds.erro(
                "NPC sem voz", "Use `!testarvoz <id>`. O NPC precisa ter o bloco `voz` no JSON."
            ))
            return
        no = conversa["nos"][conversa["inicio"]]
        texto = aplicar_variaveis(
            no.get("fala_tts") or no.get("fala") or "", conversa, "viajante", para_voz=True
        ).strip()
        if not texto:
            await ctx.send(embed=embeds.erro(
                "Nada para falar", "A primeira carta desse NPC não tem `fala`."
            ))
            return

        locutor.abrir()
        locutor.falar_em_segundo_plano(texto, conversa["voz"])
        locutor.fechar()  # o bot sai do canal depois de falar
        await ctx.send(embed=embeds.sucesso(
            "Testando a voz", f"Falando a primeira fala de **{conversa['npc']}** no canal de voz."
        ))


async def setup(bot):
    await bot.add_cog(Voz(bot))
