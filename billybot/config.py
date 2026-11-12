"""
config.py - Configurações do bot (lidas do arquivo .env).

Tudo o que muda de uma máquina para outra (token, IDs de canais, caminho do
FFmpeg) fica no .env. Os caminhos das pastas são derivados da raiz do projeto.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

RAIZ = Path(__file__).resolve().parent.parent


def _inteiro(nome: str) -> int:
    """Lê uma variável do .env como número. Ausente ou vazia vira 0."""
    return int(os.getenv(nome, "0") or 0)


@dataclass(frozen=True)
class Settings:
    token: str | None
    canal_comandos_id: int  # onde o mestre digita os comandos (0 = qualquer canal)
    canal_rpg_id: int       # onde o bot publica as conversas (0 = mesmo canal)
    voz_canal_id: int       # canal de voz do TTS (0 = voz desligada)
    ffmpeg_path: str
    caminho_env: str
    raiz: Path = RAIZ
    tempo_limite: int = 300  # segundos sem clicar até a conversa encerrar sozinha

    @property
    def pasta_dados(self) -> Path:
        return self.raiz / "data"

    @property
    def pasta_imagens(self) -> Path:
        return self.raiz / "assets" / "imagens"

    @classmethod
    def carregar(cls) -> "Settings":
        caminho = RAIZ / ".env"
        encontrado = str(caminho) if caminho.is_file() else find_dotenv(usecwd=True)
        # override=True: o .env tem prioridade sobre variáveis do sistema
        load_dotenv(encontrado or None, override=True)
        return cls(
            token=(os.getenv("DISCORD_BOT_TOKEN") or "").strip() or None,
            canal_comandos_id=_inteiro("CANAL_COMANDOS_ID"),
            canal_rpg_id=_inteiro("CANAL_RPG_ID"),
            voz_canal_id=_inteiro("VOZ_CANAL_ID"),
            ffmpeg_path=os.getenv("FFMPEG_PATH", "ffmpeg") or "ffmpeg",
            caminho_env=encontrado,
        )
