import pytest

from billybot.config import RAIZ, Settings
from billybot.core.carregador import Catalogo


@pytest.fixture(scope="session")
def catalogo():
    """Os dados reais de data/ (lidos uma vez só)."""
    return Catalogo.carregar(RAIZ / "data")


@pytest.fixture
def settings():
    return Settings(
        token="x",
        canal_comandos_id=0,
        canal_rpg_id=0,
        voz_canal_id=0,
        ffmpeg_path="ffmpeg",
        caminho_env="",
    )
