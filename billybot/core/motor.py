"""
motor.py - Regras das conversas (nenhuma linha de Discord aqui).

Separar as regras do Discord permite testar a lógica sozinha e encaixar novos
sistemas (memória de escolhas, humor, TTS) sem mexer nos botões.

A Sessao não acessa o banco de dados. Ela recebe um Contexto (marcas e itens do
jogador) e vai anotando em "eventos" o que aconteceu; quem persiste é o bot.
"""

from collections import Counter
from dataclasses import dataclass, field

RESULTADO = "@resultado"

# O que uma "variante" de nó pode trocar quando a condição "se" é atendida.
CAMPOS_DAS_VARIANTES = ("tema", "cor", "narracao", "fala", "fala_tts", "narracao_final", "itens")


def aplicar_variaveis(texto, conversa, nome_jogador, para_voz=False):
    """Troca {jogador} e as {variaveis} da conversa pelos valores reais.

    Com para_voz=True, valores só de dígitos (como um código de cofre) viram
    "5, 7, 3, 0" para a voz falar número por número em vez de "cinco mil...".
    """
    texto = texto.replace("{jogador}", nome_jogador)
    for chave, valor in conversa.get("variaveis", {}).items():
        valor = str(valor)
        if para_voz and valor.isdigit():
            valor = ", ".join(valor)
        texto = texto.replace("{" + chave + "}", valor)
    return texto


@dataclass
class Contexto:
    """O que o bot sabe sobre o jogador ao começar a conversa."""

    marcas: set = field(default_factory=set)   # escolhas marcantes já feitas
    itens: dict = field(default_factory=dict)  # id do item -> quantidade no inventário


def como_lista(valor):
    """'a' -> ['a'];  ['a', 'b'] -> ['a', 'b'];  None -> []."""
    if valor is None:
        return []
    return list(valor) if isinstance(valor, (list, tuple, set)) else [valor]


def condicao_atendida(se, contexto):
    """Confere um bloco "se". Todas as chaves presentes precisam ser verdadeiras.

        {"marca": "roubou_relogio"}      o jogador tem esta marca
        {"sem_marca": "roubou_relogio"}  o jogador NÃO tem esta marca
        {"item": "chave_escritorio"}     tem pelo menos 1 deste item
        {"sem_item": "chave_escritorio"} não tem este item

    Cada valor aceita um texto ou uma lista de textos (todos precisam valer).
    """
    if not se:
        return True
    if any(m not in contexto.marcas for m in como_lista(se.get("marca"))):
        return False
    if any(m in contexto.marcas for m in como_lista(se.get("sem_marca"))):
        return False
    if any(contexto.itens.get(i, 0) < 1 for i in como_lista(se.get("item"))):
        return False
    if any(contexto.itens.get(i, 0) >= 1 for i in como_lista(se.get("sem_item"))):
        return False
    return True


class Sessao:
    """Estado de UMA conversa em andamento (nó atual, pontos, marcas, itens)."""

    def __init__(self, conversa, contexto=None):
        self.conversa = conversa
        self.contexto = contexto if contexto is not None else Contexto()
        self.no_atual = conversa["inicio"]
        self.pontos = Counter()   # pontos por abordagem (pacifica, normal, ...)
        self.usadas = set()       # (nó, índice) das opções "uma_vez" já escolhidas
        self.humor = dict(conversa.get("humor", {}))  # valores iniciais (o item 5 vai alterá-los)
        self.reacao = None        # narração curta que abre o próximo nó
        self.encerrada = False
        self.caminho = [self.no_atual]
        self.entregues = set()    # nós que já deram itens nesta conversa
        self.marcas_novas = []    # marcas criadas nesta conversa (para o relatório)
        self.itens_dados = Counter()
        self.eventos = []         # fila do que o bot precisa gravar (ver drenar_eventos)
        self._ao_entrar(self.no_atual)

    # ------------------------------------------------------------------
    # Leitura
    # ------------------------------------------------------------------
    @property
    def no(self):
        """O nó atual já com a variante que combina com o contexto do jogador."""
        bruto = self.conversa["nos"][self.no_atual]
        for variante in bruto.get("variantes", []):
            if condicao_atendida(variante.get("se"), self.contexto):
                efetivo = dict(bruto)
                efetivo.pop("variantes", None)
                for campo in CAMPOS_DAS_VARIANTES:
                    if campo in variante:
                        efetivo[campo] = variante[campo]
                return efetivo
        return bruto

    def opcoes_visiveis(self):
        """Opções que devem aparecer como botão: lista de (índice, opção)."""
        visiveis = []
        for indice, opcao in enumerate(self.no.get("opcoes", [])):
            if opcao.get("uma_vez") and (self.no_atual, indice) in self.usadas:
                continue
            if not condicao_atendida(opcao.get("se"), self.contexto):
                continue
            visiveis.append((indice, opcao))
        return visiveis

    # ------------------------------------------------------------------
    # Escolher
    # ------------------------------------------------------------------
    def escolher(self, indice):
        """Aplica a opção clicada. Retorna True se a conversa continua."""
        no_antes = self.no_atual
        opcao = self.no["opcoes"][indice]
        if not condicao_atendida(opcao.get("se"), self.contexto):
            return True  # botão que não deveria existir: ignora

        if opcao.get("abordagem"):
            self.pontos[opcao["abordagem"]] += 1
        if opcao.get("uma_vez"):
            self.usadas.add((no_antes, indice))
        self.reacao = opcao.get("reacao")

        proximo = opcao["proximo"]
        if proximo == RESULTADO:
            proximo = self.resultado()

        self.eventos.append(("escolha", {"de": no_antes, "texto": opcao["texto"], "para": proximo}))
        for marca in como_lista(opcao.get("marca")):
            self._marcar(marca, no_antes)

        if proximo is None:  # o jogador escolheu encerrar
            self.encerrada = True
            return False

        self.no_atual = proximo
        self.caminho.append(proximo)
        self._ao_entrar(proximo)

        if not self.opcoes_visiveis():  # nó final (sem botões)
            self.encerrada = True
            return False
        return True

    def resultado(self):
        """Decide o nó final pela maior pontuação; empate no topo usa 'empate'."""
        cfg = self.conversa["pontuacao"]
        placar = {cat: self.pontos.get(cat, 0) for cat in cfg["destinos"]}
        maior = max(placar.values())
        lideres = [cat for cat, pontos in placar.items() if pontos == maior]
        escolhido = lideres[0] if len(lideres) == 1 else cfg["empate"]
        return cfg["destinos"][escolhido]

    # ------------------------------------------------------------------
    # Efeitos e memória
    # ------------------------------------------------------------------
    def _ao_entrar(self, nome_no):
        """Chegar em um nó: registra a visita, cria marcas e entrega itens (uma vez por conversa)."""
        self.eventos.append(("visita", nome_no))
        bruto = self.conversa["nos"][nome_no]
        for marca in como_lista(bruto.get("marca")):
            self._marcar(marca, nome_no)
        if bruto.get("da_itens") and nome_no not in self.entregues:
            self.entregues.add(nome_no)
            for item, quantidade in bruto["da_itens"].items():
                self.contexto.itens[item] = self.contexto.itens.get(item, 0) + quantidade
                self.itens_dados[item] += quantidade
            self.eventos.append(("itens", dict(bruto["da_itens"]), nome_no))

    def _marcar(self, marca, nome_no):
        if marca in self.contexto.marcas:
            return
        self.contexto.marcas.add(marca)
        self.marcas_novas.append(marca)
        self.eventos.append(("marca", marca, nome_no))

    def drenar_eventos(self):
        """Entrega e esvazia a fila de eventos para o bot gravar no banco.

        Tipos: ("visita", no) | ("escolha", {"de", "texto", "para"}) |
               ("marca", marca, no) | ("itens", {item: qtd}, no)
        """
        eventos, self.eventos = self.eventos, []
        return eventos

    def resumo(self):
        """Texto curto para o mestre saber como a conversa terminou."""
        linhas = [f"Caminho: {' > '.join(self.caminho)}"]
        cfg = self.conversa.get("pontuacao")
        if cfg:
            placar = " | ".join(
                f"{cat} {self.pontos.get(cat, 0)}" for cat in cfg["destinos"]
            )
            linhas.append(f"Placar: {placar}")
        if self.humor:
            linhas.append("Humor: " + " | ".join(f"{k} {v}" for k, v in self.humor.items()))
        if self.marcas_novas:
            linhas.append("Marcas novas: " + ", ".join(self.marcas_novas))
        if self.itens_dados:
            linhas.append("Itens recebidos: " + ", ".join(f"{i} x{q}" for i, q in self.itens_dados.items()))
        return "\n".join(linhas)
