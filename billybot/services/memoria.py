"""
memoria.py - Memória de escolhas (item 4).

Guarda, por jogador: cada conversa começada (execução), os nós visitados, as
escolhas feitas e as MARCAS (escolhas marcantes que mudam conversas futuras).
Os JSON usam as marcas em "se" para mostrar opções ou trocar falas.
"""

from billybot.core.motor import Contexto
from billybot.services.banco import Banco


class Memoria:
    def __init__(self, banco: Banco):
        self.banco = banco

    async def contexto(self, discord_id: int) -> Contexto:
        """Marcas e inventário do jogador, para a Sessao avaliar as condições 'se'."""
        marcas = await self.banco.consultar(
            "SELECT marca FROM marcas WHERE discord_id = ?", (discord_id,)
        )
        itens = await self.banco.consultar(
            "SELECT item, quantidade FROM inventario WHERE discord_id = ?", (discord_id,)
        )
        return Contexto(
            marcas={linha["marca"] for linha in marcas},
            itens={linha["item"]: linha["quantidade"] for linha in itens},
        )

    async def iniciar_execucao(self, discord_id: int, conversa: str) -> int:
        def operacao(conexao):
            cursor = conexao.execute(
                "INSERT INTO execucoes (discord_id, conversa) VALUES (?, ?)", (discord_id, conversa)
            )
            return cursor.lastrowid
        return await self.banco.executar(operacao)

    async def registrar(self, execucao_id: int, discord_id: int, conversa: str, eventos: list):
        """Grava os eventos da Sessao (visitas, escolhas e marcas) em uma única transação."""
        def operacao(conexao):
            for evento in eventos:
                tipo = evento[0]
                if tipo == "visita":
                    conexao.execute(
                        "INSERT INTO visitas (execucao_id, discord_id, conversa, no) VALUES (?, ?, ?, ?)",
                        (execucao_id, discord_id, conversa, evento[1]),
                    )
                elif tipo == "escolha":
                    dados = evento[1]
                    conexao.execute(
                        """INSERT INTO escolhas (execucao_id, discord_id, conversa, de_no, texto, para_no)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (execucao_id, discord_id, conversa, dados["de"], dados["texto"], dados["para"]),
                    )
                elif tipo == "marca":
                    conexao.execute(
                        "INSERT OR IGNORE INTO marcas (discord_id, marca, conversa, no) VALUES (?, ?, ?, ?)",
                        (discord_id, evento[1], conversa, evento[2]),
                    )
                # "itens" é entregue por Personagens.dar_itens, não por aqui
        await self.banco.executar(operacao)

    async def finalizar_execucao(self, execucao_id: int, final_no: str, motivo: str):
        await self.banco.executar(lambda c: c.execute(
            """UPDATE execucoes SET terminada_em = CURRENT_TIMESTAMP, final_no = ?, motivo = ?
               WHERE id = ?""",
            (final_no, motivo, execucao_id),
        ))

    # ---- marcas ----
    async def marcas(self, discord_id: int) -> list:
        return await self.banco.consultar(
            "SELECT marca, conversa, no, quando FROM marcas WHERE discord_id = ? ORDER BY quando, marca",
            (discord_id,),
        )

    async def adicionar_marca(self, discord_id: int, marca: str, conversa: str = "mestre", no: str = "") -> bool:
        """Retorna False se o jogador já tinha a marca."""
        def operacao(conexao):
            cursor = conexao.execute(
                "INSERT OR IGNORE INTO marcas (discord_id, marca, conversa, no) VALUES (?, ?, ?, ?)",
                (discord_id, marca, conversa, no),
            )
            return cursor.rowcount > 0
        return await self.banco.executar(operacao)

    async def remover_marca(self, discord_id: int, marca: str) -> bool:
        def operacao(conexao):
            cursor = conexao.execute(
                "DELETE FROM marcas WHERE discord_id = ? AND marca = ?", (discord_id, marca)
            )
            return cursor.rowcount > 0
        return await self.banco.executar(operacao)

    # ---- consulta e limpeza ----
    async def resumo(self, discord_id: int) -> list:
        """Uma linha por conversa: execuções, cartas diferentes visitadas e o último final."""
        return await self.banco.consultar(
            """SELECT e.conversa AS conversa,
                      COUNT(*) AS execucoes,
                      (SELECT COUNT(DISTINCT v.no) FROM visitas v
                        WHERE v.discord_id = e.discord_id AND v.conversa = e.conversa) AS cartas,
                      (SELECT e2.final_no FROM execucoes e2
                        WHERE e2.discord_id = e.discord_id AND e2.conversa = e.conversa
                        ORDER BY e2.id DESC LIMIT 1) AS ultimo_final
                 FROM execucoes e
                WHERE e.discord_id = ?
                GROUP BY e.conversa
                ORDER BY e.conversa""",
            (discord_id,),
        )

    async def esquecer(self, discord_id: int, conversa: str | None = None) -> dict:
        """Apaga a memória de uma conversa (ou toda a memória, se conversa for None)."""
        def operacao(conexao):
            filtro, parametros = ("", (discord_id,))
            if conversa:
                filtro, parametros = (" AND conversa = ?", (discord_id, conversa))
            execucoes = conexao.execute(
                f"DELETE FROM execucoes WHERE discord_id = ?{filtro}", parametros
            ).rowcount  # visitas e escolhas saem junto (ON DELETE CASCADE)
            marcas = conexao.execute(
                f"DELETE FROM marcas WHERE discord_id = ?{filtro}", parametros
            ).rowcount
            return {"execucoes": execucoes, "marcas": marcas}
        return await self.banco.executar(operacao)
