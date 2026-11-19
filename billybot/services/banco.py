"""
banco.py - Banco de dados SQLite do bot (itens 3 e 4).

Usa só a biblioteca padrão (sqlite3). Cada operação roda em outra thread
(asyncio.to_thread), para o bot não travar enquanto o disco responde, e abre
a sua própria conexão, o que é seguro e simples para um bot deste tamanho.

As tabelas são criadas e atualizadas por MIGRACOES. Para mudar o banco no
futuro, NUNCA edite uma migração antiga: acrescente uma nova no fim da lista.
"""

import asyncio
import sqlite3
from pathlib import Path

MIGRACOES = [
    # ---- versão 1: personagens e inventário (item 3) ----
    """
    CREATE TABLE jogadores (
        discord_id INTEGER PRIMARY KEY,
        personagem TEXT NOT NULL,
        saude      INTEGER NOT NULL,
        saude_max  INTEGER NOT NULL DEFAULT 100,
        status     TEXT NOT NULL DEFAULT 'Recém-despertado da criogenia',
        local      TEXT NOT NULL DEFAULT 'Subsolo 57',
        criado_em  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE inventario (
        discord_id INTEGER NOT NULL REFERENCES jogadores(discord_id) ON DELETE CASCADE,
        item       TEXT NOT NULL,
        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
        PRIMARY KEY (discord_id, item)
    );
    """,
    # ---- versão 2: memória de escolhas (item 4) ----
    """
    CREATE TABLE execucoes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id  INTEGER NOT NULL,
        conversa    TEXT NOT NULL,
        iniciada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        terminada_em TEXT,
        final_no    TEXT,
        motivo      TEXT
    );
    CREATE TABLE visitas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        execucao_id INTEGER NOT NULL REFERENCES execucoes(id) ON DELETE CASCADE,
        discord_id  INTEGER NOT NULL,
        conversa    TEXT NOT NULL,
        no          TEXT NOT NULL,
        quando      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE escolhas (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        execucao_id INTEGER NOT NULL REFERENCES execucoes(id) ON DELETE CASCADE,
        discord_id  INTEGER NOT NULL,
        conversa    TEXT NOT NULL,
        de_no       TEXT NOT NULL,
        texto       TEXT NOT NULL,
        para_no     TEXT,
        quando      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE marcas (
        discord_id INTEGER NOT NULL,
        marca      TEXT NOT NULL,
        conversa   TEXT NOT NULL,
        no         TEXT NOT NULL,
        quando     TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (discord_id, marca)
    );
    CREATE INDEX idx_execucoes_jogador ON execucoes (discord_id);
    CREATE INDEX idx_visitas_execucao ON visitas (execucao_id);
    CREATE INDEX idx_escolhas_execucao ON escolhas (execucao_id);
    """,
]


class Banco:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def _conectar(self) -> sqlite3.Connection:
        conexao = sqlite3.connect(self.caminho, timeout=10)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    def _rodar(self, funcao):
        conexao = self._conectar()
        try:
            with conexao:  # confirma (commit) no fim, ou desfaz (rollback) se der erro
                return funcao(conexao)
        finally:
            conexao.close()

    async def executar(self, funcao):
        """Roda funcao(conexao) em outra thread, dentro de uma transação."""
        return await asyncio.to_thread(self._rodar, funcao)

    async def consultar(self, sql: str, parametros=()) -> list:
        """SELECT que devolve uma lista de dicionários."""
        def operacao(conexao):
            return [dict(linha) for linha in conexao.execute(sql, parametros).fetchall()]
        return await self.executar(operacao)

    async def consultar_um(self, sql: str, parametros=()):
        """SELECT que devolve um dicionário (ou None)."""
        linhas = await self.consultar(sql, parametros)
        return linhas[0] if linhas else None

    async def iniciar(self) -> int:
        """Cria a pasta e as tabelas (ou atualiza). Retorna a versão do banco."""
        self.caminho.parent.mkdir(parents=True, exist_ok=True)

        def operacao(conexao):
            conexao.execute("PRAGMA journal_mode = WAL")
            atual = conexao.execute("PRAGMA user_version").fetchone()[0]
            for numero in range(atual, len(MIGRACOES)):
                # BEGIN/COMMIT dentro do script: a migração inteira vale ou nada vale
                conexao.executescript(
                    f"BEGIN;\n{MIGRACOES[numero]}\nPRAGMA user_version = {numero + 1};\nCOMMIT;"
                )
            return conexao.execute("PRAGMA user_version").fetchone()[0]

        return await self.executar(operacao)
