"""
personagens.py - Ficha de personagem e inventário (item 3).
"""

import re

from billybot.services.banco import Banco


class PersonagemInexistente(Exception):
    """O jogador ainda não tem personagem (use !personagem)."""


class ItemInsuficiente(Exception):
    """O jogador não tem a quantidade pedida do item."""


PADRAO_SAUDE = re.compile(r"^\s*([+\-=]?)\s*(\d+)\s*$")


def interpretar_saude(texto: str):
    """'+10' -> ('+', 10) | '-5' -> ('-', 5) | '=80' ou '80' -> ('=', 80). Erro: ValueError."""
    achou = PADRAO_SAUDE.match(texto or "")
    if not achou:
        raise ValueError("use +N (curar), -N (ferir) ou =N (definir). Exemplo: -15")
    return (achou.group(1) or "="), int(achou.group(2))


class Personagens:
    def __init__(self, banco: Banco):
        self.banco = banco

    async def obter(self, discord_id: int):
        return await self.banco.consultar_um(
            "SELECT * FROM jogadores WHERE discord_id = ?", (discord_id,)
        )

    async def criar(self, discord_id: int, nome: str, saude_max: int = 100):
        """Cria o personagem (com saúde cheia) ou só troca o nome se ele já existe."""
        def operacao(conexao):
            conexao.execute(
                """INSERT INTO jogadores (discord_id, personagem, saude, saude_max)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(discord_id) DO UPDATE SET personagem = excluded.personagem""",
                (discord_id, nome.strip(), saude_max, saude_max),
            )
        await self.banco.executar(operacao)
        return await self.obter(discord_id)

    async def ajustar_saude(self, discord_id: int, modo: str, valor: int) -> int:
        """modo '+' cura, '-' fere, '=' define. A saúde fica entre 0 e a saúde máxima."""
        def operacao(conexao):
            linha = conexao.execute(
                "SELECT saude, saude_max FROM jogadores WHERE discord_id = ?", (discord_id,)
            ).fetchone()
            if linha is None:
                raise PersonagemInexistente(discord_id)
            nova = {"+": linha["saude"] + valor, "-": linha["saude"] - valor, "=": valor}[modo]
            nova = max(0, min(linha["saude_max"], nova))
            conexao.execute("UPDATE jogadores SET saude = ? WHERE discord_id = ?", (nova, discord_id))
            return nova
        return await self.banco.executar(operacao)

    async def _atualizar_texto(self, discord_id: int, campo: str, texto: str):
        assert campo in ("status", "local")  # nunca monte SQL com texto vindo de fora
        def operacao(conexao):
            cursor = conexao.execute(
                f"UPDATE jogadores SET {campo} = ? WHERE discord_id = ?", (texto.strip(), discord_id)
            )
            if cursor.rowcount == 0:
                raise PersonagemInexistente(discord_id)
        await self.banco.executar(operacao)

    async def definir_status(self, discord_id: int, texto: str):
        await self._atualizar_texto(discord_id, "status", texto)

    async def definir_local(self, discord_id: int, texto: str):
        await self._atualizar_texto(discord_id, "local", texto)

    # ---- inventário ----
    async def inventario(self, discord_id: int) -> dict:
        linhas = await self.banco.consultar(
            "SELECT item, quantidade FROM inventario WHERE discord_id = ? ORDER BY item", (discord_id,)
        )
        return {linha["item"]: linha["quantidade"] for linha in linhas}

    async def dar_itens(self, discord_id: int, itens: dict) -> dict:
        """Soma vários itens de uma vez ({id: quantidade}). Retorna o inventário atualizado."""
        def operacao(conexao):
            if conexao.execute(
                "SELECT 1 FROM jogadores WHERE discord_id = ?", (discord_id,)
            ).fetchone() is None:
                raise PersonagemInexistente(discord_id)
            for item, quantidade in itens.items():
                conexao.execute(
                    """INSERT INTO inventario (discord_id, item, quantidade) VALUES (?, ?, ?)
                       ON CONFLICT(discord_id, item) DO UPDATE SET quantidade = quantidade + excluded.quantidade""",
                    (discord_id, item, quantidade),
                )
        await self.banco.executar(operacao)
        return await self.inventario(discord_id)

    async def dar_item(self, discord_id: int, item: str, quantidade: int = 1) -> int:
        inventario = await self.dar_itens(discord_id, {item: quantidade})
        return inventario[item]

    async def tirar_item(self, discord_id: int, item: str, quantidade: int = 1) -> int:
        """Retira itens. Retorna quantos sobraram. Erro: ItemInsuficiente."""
        def operacao(conexao):
            if conexao.execute(
                "SELECT 1 FROM jogadores WHERE discord_id = ?", (discord_id,)
            ).fetchone() is None:
                raise PersonagemInexistente(discord_id)
            linha = conexao.execute(
                "SELECT quantidade FROM inventario WHERE discord_id = ? AND item = ?", (discord_id, item)
            ).fetchone()
            tem = linha["quantidade"] if linha else 0
            if tem < quantidade:
                raise ItemInsuficiente(f"tem {tem}, pediu {quantidade}")
            sobra = tem - quantidade
            if sobra:
                conexao.execute(
                    "UPDATE inventario SET quantidade = ? WHERE discord_id = ? AND item = ?",
                    (sobra, discord_id, item),
                )
            else:
                conexao.execute(
                    "DELETE FROM inventario WHERE discord_id = ? AND item = ?", (discord_id, item)
                )
            return sobra
        return await self.banco.executar(operacao)
