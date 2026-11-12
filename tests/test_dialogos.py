import asyncio
import dataclasses
import inspect
import json
import shutil
from types import SimpleNamespace
from unittest.mock import AsyncMock

from discord.ext import commands

from billybot.bot import BillyBot
from billybot.config import RAIZ, Settings
from billybot.core.carregador import Catalogo
from billybot.diagnostico import resumo_de_inicializacao

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154"
    "789c6360000002000001e221bc330000000049454e44ae426082"
)
JOGADOR = SimpleNamespace(display_name="Alan", id=1)


def _ctx(canal_id=5):
    canal = SimpleNamespace(id=canal_id, send=AsyncMock(return_value=SimpleNamespace()), mention="#canal")
    ctx = SimpleNamespace(channel=canal, send=AsyncMock(), author=SimpleNamespace(mention="@mestre"))
    return ctx, canal


async def _bot_pronto(settings, catalogo):
    bot = BillyBot(settings, catalogo)
    await bot.setup_hook()  # carrega os cogs
    return bot


def _clicar_tudo(view):
    """Escolhe sempre a primeira opção até a conversa terminar."""
    async def correr():
        interacao = SimpleNamespace(
            user=JOGADOR,
            response=SimpleNamespace(edit_message=AsyncMock(), send_message=AsyncMock()),
        )
        for _ in range(30):
            if view.sessao.encerrada:
                break
            await view.escolher(interacao, view.children[0].indice)
    return correr()


def test_cogs_registram_os_comandos(settings, catalogo):
    async def main():
        bot = await _bot_pronto(settings, catalogo)
        esperados = {"deuzebio", "stefano", "sobrevivente", "prologo",
                     "falar", "conversas", "recarregar", "vozes", "testarvoz"}
        assert esperados <= set(bot.all_commands)
        assert {"Dialogos", "Voz", "Erros"} <= set(bot.cogs)
    asyncio.run(main())


def test_iniciar_no_mesmo_canal(settings, catalogo):
    async def main():
        bot = await _bot_pronto(settings, catalogo)
        ctx, canal = _ctx()
        await bot.get_cog("Dialogos").iniciar(ctx, "deuzebio", JOGADOR)
        kw = canal.send.await_args.kwargs
        assert kw["embed"].title == "Deuzébio Barbosa"  # sem foto na pasta, mostra o título
        assert len(kw["view"].children) == 3
        ctx.send.assert_not_awaited()  # mesmo canal: sem aviso extra nem relatório
        assert kw["view"].canal_mestre is None
    asyncio.run(main())


def test_iniciar_em_outro_canal_avisa_o_mestre_e_manda_relatorio(settings, catalogo):
    async def main():
        bot = await _bot_pronto(dataclasses.replace(settings, canal_rpg_id=9), catalogo)
        rpg = SimpleNamespace(id=9, send=AsyncMock(return_value=SimpleNamespace()), mention="#rpg")
        bot.get_channel = lambda canal_id: rpg if canal_id == 9 else None
        ctx, comandos = _ctx(canal_id=5)

        await bot.get_cog("Dialogos").iniciar(ctx, "deuzebio", JOGADOR)
        rpg.send.assert_awaited_once()
        assert "Conversa publicada" in ctx.send.await_args.kwargs["embed"].title

        view = rpg.send.await_args.kwargs["view"]
        await _clicar_tudo(view)
        texto = comandos.send.await_args.args[0]
        assert "terminou" in texto and "Caminho:" in texto and "Placar:" in texto
    asyncio.run(main())


def test_canal_do_rpg_inexistente(settings, catalogo):
    async def main():
        bot = await _bot_pronto(dataclasses.replace(settings, canal_rpg_id=9), catalogo)
        bot.get_channel = lambda canal_id: None
        ctx, canal = _ctx()
        await bot.get_cog("Dialogos").iniciar(ctx, "deuzebio", None)
        canal.send.assert_not_awaited()
        assert "Canal do RPG não encontrado" in ctx.send.await_args.kwargs["embed"].title
    asyncio.run(main())


def test_foto_do_npc_vai_anexada_e_vira_autor_do_embed(settings, catalogo, tmp_path):
    async def main():
        pasta = tmp_path / "assets" / "imagens"
        pasta.mkdir(parents=True)
        (pasta / "Deuzébio Babosa.png").write_bytes(PNG)
        bot = await _bot_pronto(dataclasses.replace(settings, raiz=tmp_path), catalogo)
        ctx, canal = _ctx()
        await bot.get_cog("Dialogos").iniciar(ctx, "deuzebio", JOGADOR)
        kw = canal.send.await_args.kwargs
        assert kw["file"].filename == "avatar.png"
        assert kw["embed"].author.name == "Deuzébio Barbosa"
        assert kw["embed"].author.icon_url == "attachment://avatar.png"
    asyncio.run(main())


def test_falar_pelo_id(settings, catalogo):
    async def main():
        bot = await _bot_pronto(settings, catalogo)
        cog = bot.get_cog("Dialogos")
        ctx, canal = _ctx()
        await cog.falar.callback(cog, ctx, "ESTEFANO", None)  # id que não existe
        assert "não encontrada" in ctx.send.await_args.kwargs["embed"].title
        await cog.falar.callback(cog, ctx, "Stefano", None)   # maiúsculas são aceitas
        assert canal.send.await_args.kwargs["embed"].title == "Stefano Sero"
    asyncio.run(main())


def test_comando_conversas_lista_tudo(settings, catalogo):
    async def main():
        bot = await _bot_pronto(settings, catalogo)
        cog = bot.get_cog("Dialogos")
        ctx, _ = _ctx()
        await cog.conversas.callback(cog, ctx)
        descricao = ctx.send.await_args.kwargs["embed"].description
        assert all(f"`!{chave} [@jogador]`" in descricao for chave in catalogo.conversas)
    asyncio.run(main())


def test_recarregar_adiciona_remove_e_protege_contra_json_quebrado(settings, tmp_path):
    shutil.copytree(RAIZ / "data", tmp_path / "data")
    novo = tmp_path / "data" / "npcs" / "novo.json"

    async def main():
        s = dataclasses.replace(settings, raiz=tmp_path)
        bot = await _bot_pronto(s, Catalogo.carregar(s.pasta_dados))
        cog = bot.get_cog("Dialogos")
        ctx, _ = _ctx()
        assert "novo" not in bot.all_commands

        # 1) arquivo novo vira comando sem reiniciar
        novo.write_text(json.dumps({
            "npc": "Novo", "descricao": "Teste.", "inicio": "a",
            "nos": {"a": {"narracao": "Oi.", "opcoes": [{"texto": "Tchau.", "proximo": None}]}},
        }), encoding="utf-8")
        await cog.recarregar.callback(cog, ctx)
        assert "novo" in bot.all_commands and "novo" in bot.catalogo.conversas
        assert "Dados recarregados" in ctx.send.await_args.kwargs["embed"].title

        # 2) JSON quebrado: nada muda e o erro é explicado
        novo.write_text('{"npc": ', encoding="utf-8")
        await cog.recarregar.callback(cog, ctx)
        embed = ctx.send.await_args.kwargs["embed"]
        assert "Nada foi recarregado" in embed.title and "novo.json" in embed.description
        assert "novo" in bot.all_commands  # o catálogo antigo continua valendo

        # 3) arquivo apagado: o comando some
        novo.unlink()
        await cog.recarregar.callback(cog, ctx)
        assert "novo" not in bot.all_commands and "deuzebio" in bot.all_commands
    asyncio.run(main())


def test_somente_o_canal_de_comandos(settings, catalogo):
    async def main():
        bot = BillyBot(dataclasses.replace(settings, canal_comandos_id=7), catalogo)
        assert await bot._somente_canal_de_comandos(SimpleNamespace(channel=SimpleNamespace(id=7)))
        assert not await bot._somente_canal_de_comandos(SimpleNamespace(channel=SimpleNamespace(id=8)))
        livre = BillyBot(settings, catalogo)  # 0 = qualquer canal
        assert await livre._somente_canal_de_comandos(SimpleNamespace(channel=SimpleNamespace(id=8)))
    asyncio.run(main())


def test_erros_amigaveis(settings, catalogo):
    async def main():
        bot = await _bot_pronto(dataclasses.replace(settings, canal_comandos_id=7), catalogo)
        cog = bot.get_cog("Erros")
        ctx, _ = _ctx()
        ctx.command = SimpleNamespace(qualified_name="falar", signature="<chave> [jogador]")

        await cog.on_command_error(ctx, commands.CommandNotFound("x"))
        ctx.send.assert_not_awaited()

        await cog.on_command_error(ctx, commands.CheckFailure("x"))
        assert "Canal errado" in ctx.send.await_args.kwargs["embed"].title

        await cog.on_command_error(ctx, commands.BadArgument("x"))
        assert "Jogador não encontrado" in ctx.send.await_args.kwargs["embed"].title

        parametro = commands.Parameter(name="chave", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
        await cog.on_command_error(ctx, commands.MissingRequiredArgument(parametro))
        assert "!falar <chave> [jogador]" in ctx.send.await_args.kwargs["embed"].description
    asyncio.run(main())


def test_settings_le_o_env_e_limpa_espacos(monkeypatch):
    import billybot.config as config
    monkeypatch.setattr(config, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(config, "find_dotenv", lambda **k: "")
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "  abc.def  ")
    monkeypatch.setenv("CANAL_RPG_ID", "123")
    monkeypatch.setenv("VOZ_CANAL_ID", "")
    monkeypatch.delenv("CANAL_COMANDOS_ID", raising=False)
    s = Settings.carregar()
    assert s.token == "abc.def" and s.canal_rpg_id == 123
    assert s.voz_canal_id == 0 and s.canal_comandos_id == 0
    assert s.pasta_dados == RAIZ / "data"


def test_resumo_de_inicializacao(settings, catalogo):
    linhas = resumo_de_inicializacao(settings, catalogo)
    texto = "\n".join(linhas)
    assert "Conversas (4)" in texto and "Temas (7)" in texto
    assert "Voz TTS desligada" in texto
    ligada = resumo_de_inicializacao(dataclasses.replace(settings, voz_canal_id=1), catalogo)
    assert any("Voz TTS ligada" in linha for linha in ligada)
