"""
main.py - Ponto de entrada do BillyBot.

    python main.py
"""

import discord

from billybot.bot import BillyBot
from billybot.config import Settings
from billybot.core.carregador import Catalogo
from billybot.diagnostico import resumo_de_inicializacao


def main() -> None:
    discord.utils.setup_logging()  # mensagens de log no terminal

    settings = Settings.carregar()
    catalogo = Catalogo.carregar(settings.pasta_dados)

    if catalogo.erros:
        print("Erros encontrados nos arquivos de data/:")
        for erro in catalogo.erros:
            print(" -", erro)
        raise SystemExit(1)

    if not settings.token:
        raise SystemExit("DISCORD_BOT_TOKEN não encontrado. Confira o arquivo .env")

    for linha in resumo_de_inicializacao(settings, catalogo):
        print(linha)

    bot = BillyBot(settings, catalogo)
    try:
        bot.run(settings.token, log_handler=None)
    except discord.LoginFailure:
        print("Token recusado pelo Discord (401).")
        print(f"  .env usado: {settings.caminho_env or 'NENHUM ENCONTRADO'}")
        print(f"  tamanho do token: {len(settings.token)} | pontos: {settings.token.count('.')}")
        print("  Um token de bot costuma ter ~70 caracteres e 2 pontos.")
        raise SystemExit(
            "Gere um novo em Developer Portal > Bot > Reset Token, cole no "
            ".env sem aspas nem espaços e tente novamente."
        )


if __name__ == "__main__":
    main()
