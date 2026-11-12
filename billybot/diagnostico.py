"""
diagnostico.py - Resumo mostrado no terminal ao ligar o bot.
"""

import importlib.util
import shutil
import sys
from pathlib import Path

from billybot import __version__
from billybot.services.avatares import localizar_avatar


def resumo_de_inicializacao(settings, catalogo):
    """Retorna as linhas que o main.py imprime antes de conectar ao Discord."""
    linhas = [
        f"BillyBot {__version__}",
        f".env usado: {settings.caminho_env or 'nenhum encontrado'}",
        f"Conversas ({len(catalogo.conversas)}): {', '.join(catalogo.conversas) or 'nenhuma'}",
        f"Temas ({len(catalogo.temas)}): {', '.join(catalogo.temas)}",
    ]
    linhas += [f"Aviso: {aviso}" for aviso in catalogo.avisos]

    com_foto, sem_foto = [], []
    for chave, conversa in catalogo.conversas.items():
        arquivo, url = localizar_avatar(chave, conversa, settings.raiz, settings.pasta_imagens)
        (com_foto if (arquivo or url) else sem_foto).append(chave)
        if conversa.get("avatar") and not (arquivo or url):
            linhas.append(f"Aviso: o avatar '{conversa['avatar']}' de '{chave}' não foi encontrado.")
    linhas.append("NPCs com foto: " + (", ".join(com_foto) or "nenhum"))
    if sem_foto:
        linhas.append("NPCs sem foto (coloque assets/imagens/<id>.png): " + ", ".join(sem_foto))

    if settings.voz_canal_id:
        faltando = [
            pacote
            for modulo, pacote in (("edge_tts", "edge-tts"), ("nacl", "PyNaCl"))
            if importlib.util.find_spec(modulo) is None
        ]
        if faltando:
            linhas.append(f"Aviso: pacote(s) não encontrado(s) neste Python: {', '.join(faltando)}")
            linhas.append(f"  Python em uso: {sys.executable}")
            linhas.append(f'  Na pasta do projeto, rode: "{sys.executable}" -m pip install -r requirements.txt')
        if shutil.which(settings.ffmpeg_path) is None and not Path(settings.ffmpeg_path).is_file():
            linhas.append(f"Aviso: FFmpeg não encontrado ('{settings.ffmpeg_path}'). A voz não vai funcionar.")
        falantes = [chave for chave, conversa in catalogo.conversas.items() if conversa.get("voz")]
        linhas.append("Voz TTS ligada. NPCs com voz: " + (", ".join(falantes) or "nenhum"))
    else:
        linhas.append("Voz TTS desligada (defina VOZ_CANAL_ID no .env para ligar).")
    return linhas
