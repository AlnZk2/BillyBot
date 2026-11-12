"""
avatares.py - Acha a foto de perfil de cada NPC.
"""

from pathlib import Path

EXTENSOES_IMAGEM = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def localizar_avatar(chave, conversa, raiz, pasta_imagens):
    """Retorna (arquivo_local, url); ambos podem ser None.

    Ordem de busca:
      1. campo "avatar" da conversa: um link (https://...) ou um caminho
         relativo à raiz do projeto (ex.: "assets/imagens/velho.png");
      2. arquivo assets/imagens/<id>.png (ou .jpg, .jpeg, .webp, .gif).
    """
    avatar = conversa.get("avatar")
    if avatar and avatar.startswith(("http://", "https://")):
        return None, avatar
    if avatar:
        caminho = Path(raiz) / avatar
        return (caminho, None) if caminho.is_file() else (None, None)
    for extensao in EXTENSOES_IMAGEM:
        caminho = Path(pasta_imagens) / f"{chave}{extensao}"
        if caminho.is_file():
            return caminho, None
    return None, None
