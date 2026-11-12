import asyncio
import copy
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock

from billybot.bot import BillyBot
from billybot.services import tts
from billybot.ui.views import DialogoView

JOGADOR = SimpleNamespace(display_name="Alan", id=1)


class VCFalso:
    def __init__(self):
        self.tocando = False
        self.fontes = []
        self.stop_chamado = 0
        self.disconnect = AsyncMock()

    def is_playing(self):
        return self.tocando

    def stop(self):
        self.stop_chamado += 1
        self.tocando = False

    def play(self, fonte, after=None):
        self.fontes.append((fonte, after))
        self.tocando = True


def _locutor(vc):
    loc = tts.Locutor(SimpleNamespace(), 99, "ffmpeg")
    loc._conectar = AsyncMock(return_value=vc)
    loc._voice_client = lambda: vc
    loc._criar_origem = lambda arquivo: ("fonte", arquivo)
    return loc


def _sintese_falsa(tmp_path, atrasos=None):
    async def sintese(texto, voz):
        await asyncio.sleep((atrasos or {}).get(texto, 0))
        caminho = tmp_path / f"npc_{texto}.mp3"
        caminho.write_bytes(b"x")
        return str(caminho)
    return sintese


def test_a_fala_mais_nova_vence_e_os_temporarios_sao_apagados(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "sintetizar", _sintese_falsa(tmp_path, {"lenta": 0.25, "rapida": 0.02}))

    async def main():
        vc = VCFalso()
        loc = _locutor(vc)
        loc.abrir()
        loc.falar_em_segundo_plano("lenta", {})
        loc.falar_em_segundo_plano("rapida", {})
        await asyncio.sleep(0.4)
        assert len(vc.fontes) == 1 and vc.fontes[0][0][1].endswith("rapida.mp3")
        assert not (tmp_path / "npc_lenta.mp3").exists()  # descartado
        vc.fontes[0][1](None)                              # fim da reprodução
        assert not (tmp_path / "npc_rapida.mp3").exists()
    asyncio.run(main())


def test_nova_fala_interrompe_a_que_esta_tocando(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "sintetizar", _sintese_falsa(tmp_path))

    async def main():
        vc = VCFalso()
        vc.tocando = True
        loc = _locutor(vc)
        loc.falar_em_segundo_plano("seguinte", {})
        await asyncio.sleep(0.1)
        assert vc.stop_chamado == 1 and len(vc.fontes) == 1
    asyncio.run(main())


def test_sai_do_canal_quando_a_ultima_conversa_termina(monkeypatch, tmp_path):
    monkeypatch.setattr(tts, "sintetizar", _sintese_falsa(tmp_path))

    async def main():
        vc = VCFalso()
        loc = _locutor(vc)
        loc.abrir()
        loc.fechar()
        await asyncio.sleep(3)
        vc.disconnect.assert_awaited_once()
    asyncio.run(main())


def test_conversa_nova_cancela_a_saida(monkeypatch, tmp_path):
    async def main():
        vc = VCFalso()
        loc = _locutor(vc)
        loc.abrir()
        loc.fechar()
        loc.abrir()
        await asyncio.sleep(3)
        vc.disconnect.assert_not_awaited()
    asyncio.run(main())


def test_falha_na_sintese_nao_derruba_nada(monkeypatch):
    async def quebra(texto, voz):
        raise RuntimeError("sem internet")
    monkeypatch.setattr(tts, "sintetizar", quebra)

    async def main():
        loc = _locutor(VCFalso())
        loc.falar_em_segundo_plano("x", {})
        await asyncio.sleep(0.1)
        assert loc._pendentes == 0
    asyncio.run(main())


def test_mensagem_de_erro_do_edge_tts_mostra_o_python_em_uso(monkeypatch):
    import sys
    monkeypatch.setitem(sys.modules, "edge_tts", None)
    try:
        tts._edge_tts()
    except RuntimeError as erro:
        assert sys.executable in str(erro) and "-m pip install" in str(erro)
    else:
        raise AssertionError("deveria ter falhado")


# ---------------------------------------------------------------- o que vai para a voz
class LocutorGravador:
    def __init__(self, ligado=True):
        self.ligado = ligado
        self.falas = []
        self.aberturas = 0
        self.fechamentos = 0

    def abrir(self):
        self.aberturas += 1

    def fechar(self):
        self.fechamentos += 1

    def falar_em_segundo_plano(self, texto, voz):
        self.falas.append((texto, voz))


def _interacao():
    return SimpleNamespace(
        user=JOGADOR,
        response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock()),
    )


def test_so_a_fala_vai_para_a_voz(settings, catalogo):
    async def main():
        bot = BillyBot(settings, catalogo)
        bot.locutor = LocutorGravador()
        conversa = catalogo.conversas["deuzebio"]
        view = DialogoView(bot, conversa, JOGADOR)
        await view.abrir_voz()

        texto, voz = bot.locutor.falas[0]
        assert texto == "Então uma delas falhou... Alguém finalmente acordou lá dentro. Quem é você, guri?"
        assert "No chão frio" not in texto and "Os olhos" not in texto  # narração nunca é falada
        assert voz["velocidade"] == "-22%"

        interacao = _interacao()

        async def clicar(trecho):
            for botao in view.children:
                if trecho in botao.label:
                    return await view.escolher(interacao, botao.indice)
            raise AssertionError(trecho)

        await view.escolher(interacao, view.children[0].indice)
        await view.escolher(interacao, view.children[0].indice)
        antes = len(bot.locutor.falas)
        await clicar("???")
        assert len(bot.locutor.falas) == antes, "nó sem fala fica em silêncio"
        await clicar("Paraíso")
        await view.escolher(interacao, 0)
        final = bot.locutor.falas[-1][0]
        assert "5, 7, 3, 0" in final and "Com esforço" not in final
        assert (bot.locutor.aberturas, bot.locutor.fechamentos) == (1, 1)
    asyncio.run(main())


def test_encerrar_nao_repete_a_fala_mas_fecha_a_voz(settings, catalogo):
    async def main():
        bot = BillyBot(settings, catalogo)
        bot.locutor = LocutorGravador()
        view = DialogoView(bot, catalogo.conversas["stefano"], JOGADOR)
        await view.abrir_voz()
        antes = len(bot.locutor.falas)
        for botao in view.children:
            if "Preciso ir" in botao.label:
                await view.escolher(_interacao(), botao.indice)
        assert len(bot.locutor.falas) == antes and bot.locutor.fechamentos == 1
    asyncio.run(main())


def test_voz_desligada_ou_npc_sem_voz_fica_em_silencio(settings, catalogo):
    async def main():
        bot = BillyBot(settings, catalogo)
        bot.locutor = LocutorGravador(ligado=False)
        await DialogoView(bot, catalogo.conversas["deuzebio"], JOGADOR).abrir_voz()
        assert bot.locutor.falas == [] and bot.locutor.aberturas == 0

        bot.locutor = LocutorGravador()
        sem_voz = copy.deepcopy(catalogo.conversas["stefano"])
        sem_voz.pop("voz")
        await DialogoView(bot, sem_voz, JOGADOR).abrir_voz()
        assert bot.locutor.falas == []
    asyncio.run(main())


def test_prologo_so_fala_as_falas(settings, catalogo):
    async def main():
        bot = BillyBot(settings, catalogo)
        bot.locutor = LocutorGravador()
        view = DialogoView(bot, catalogo.conversas["prologo"], None)
        await view.abrir_voz()
        assert bot.locutor.falas[0][0] == "Quanto tempo eu dormi?"
        assert bot.locutor.falas[0][1]["nome"] == "pt-BR-FranciscaNeural"
    asyncio.run(main())
