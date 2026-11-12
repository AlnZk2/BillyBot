# CONTEXTO DE SUA CRIAÇÃO

### Relato do criador/desenvolvedor

Tudo começou quando um grupo de amigos comentava sobre mesas de RPG, logo me prontifiquei dizendo que já havia participado de diversos RPGs, especialmente sobre a temática apocalíptica. Tempo depois, com uma história feita e alguns NPCs criados, me veio uma ideia: "Não sei muito bem fazer um personagem...Porque não criar um BOT que simule os NPCs que nem os jogos de Fallout que tem como tu clicar nas opções de diálogo?" Desde então, cada dia venho conferir meu bot, adicionar algo novo nele e aperfeiçoar cada vez mais nele, claro, esse bot foi feito com ajuda do Claude para criar toda a estrutura dele e o ChatGPT para criar as artes dos personagens. Bom, meu sonho era criar meu próprio RPG e ser um mestre para uma história que havia criado para entreter e viver alguns momentos com meus amigos e que talvez isso ajude também outros mestres de RPG em inovar no conceito de trazer NPCs/Personagens do mestre. Espero que aproveite e goste da minha criação!

*Ass: AlnZk2 - The Wizard* 👻

# SUBSOLO 57

### LORE

O ano é 2030, o mundo entrou em colapso, a civilização entrou em pânico em decorrência de uma pandemia crescente relacionada a um vírus vindo de fungos, junto a isso, já ocorria problemas relacionadas a crises entre países, logo após confrontos longos, a opção dada pelo governo era simplesmente, explodir tudo e montar quarentenas, conhecidos como subsolos, esses subsolos comportavam famílias e moradores que viviam em regiões demarcadas, cada subsolo representava uma cidade, os que ficavam para trás, tinham que sobreviver no solo, mas não sobreviveram nem 1 dia em decorrência das mutações, que eram o principal perigo da humanidade após a explosão da 3° guerra mundial.

Alguns humanos se uniram e montaram clãs, como grupos de civis gentis que montaram uma civilização, militares que combatem as tais pragas, as facções que cobram dos sobreviventes e alguns mistérios que habitam o cotidiano das pessoas

Os Subsolos possuem números, que representam a região (Norte, Nordeste, Centro-Oeste, Sudeste e Sul) e o subsolo (dependendo da demanda e número de pessoas)

### COMO COMEÇA O RPG?

Você começa acordando em um subsolo conhecido como Subsolo 57, localizado no centro do Rio Grande do Sul, não lembra de muita coisa sobre seu passado, mas lembra que recebeu um convite para se abrigar no subsolo caso um alarme emergencial tocasse e dias depois, uma das bombas foi detectada se aproximando na cidade, após isso, resolveu correr em direção ao abrigo, só que não sabia que esse tal abrigo era um experimento de criogenia, ficando congelado por anos, ou seja, se passaram 125 anos após o ocorrido, assim, acordando depois que a câmara de criogênio apresentou um defeito que o fez acordar de repente, nesse abrigo, encontra outras pessoas congeladas. E assim, começa a sua história

# Subsolo 57 – Bot de NPCs para Discord

## Sobre o projeto

Bot de Discord (**BillyBot**) para a mesa de RPG **Subsolo 57**. Ele funciona como um NPC
interativo: o mestre cadastra conversas, cada conversa vira um comando, e o
jogador responde clicando em botões, no estilo das rodas de diálogo dos RPGs
triple A.

O bot **não usa IA nem API externa**. Todas as falas são escritas pelo mestre.

O mestre digita o comando em um canal próprio (o canal de comandos) e o bot
publica a conversa no canal do RPG, onde os jogadores respondem.

A partir da versão 2.0.0, os textos das conversas ficam em arquivos **JSON** (pasta `data/`)
e o código é dividido em **cogs** (módulos do `discord.py`), para que novos sistemas
possam ser adicionados sem mexer no que já funciona.

## Funcionalidades

- Uma conversa por arquivo JSON, e cada uma vira um comando (`!deuzebio`, `!stefano`, `!prologo`, ...).
- Textos fora do código: NPCs em `data/npcs/` e histórias em `data/story/`.
- `!recarregar` relê os JSON sem reiniciar o bot e avisa o erro exato (arquivo, linha e coluna) se algo estiver quebrado.
- O mestre digita o comando no canal de comandos e o bot responde no canal do RPG.
- Diálogo em árvore: cada fala do NPC tem opções de resposta em botões.
- Embeds com temas visuais (azul criogênico, vermelho de perigo, verde de área segura), que podem mudar a cada carta.
- Sistema de abordagens: cada resposta soma pontos (pacífica, normal, agressiva)
  sem aparecer escrito para o jogador, e o final é decidido pela maioria.
- Opções ocultas de uso único (usadas, por exemplo, para o diálogo secreto).
- Texto separado em narração e fala: o TTS fala só a fala, nunca a narração.
- Foto de perfil do NPC ao lado do nome em cada fala (arquivo na pasta `assets/imagens/` ou link).
- Voz TTS: o bot entra no canal de voz e fala a `fala` de cada carta, com uma voz
  diferente (velocidade e tom) para cada NPC. Desligada por padrão.
- Itens obtidos aparecem no fim da conversa.
- Relatório privado para o mestre, no canal de comandos, quando a conversa termina.
- Restrição ao canal de comandos definido pelo mestre.
- Marcando um jogador (`!comando @jogador`), só ele pode clicar nos botões.
  Sem marcar, qualquer pessoa do canal pode responder.
- Conversa encerra sozinha após 5 minutos sem resposta.
- Validação automática dos JSON ao ligar o bot (links quebrados, temas inexistentes, nós sem saída).
- Suíte de testes automáticos (`python -m pytest`).

## Estrutura de arquivos

```
BillyBot/
├── main.py                  # ponto de entrada: python main.py
├── requirements.txt         # dependências do bot
├── requirements-dev.txt     # dependências dos testes
├── pytest.ini
├── .env.example             # modelo de configuração
├── .gitignore
├── README.md
├── billybot/                # o código, dividido por responsabilidade
│   ├── __init__.py          # versão do bot
│   ├── bot.py               # classe BillyBot: junta configurações, dados e cogs
│   ├── config.py            # lê o .env (token, canais, FFmpeg)
│   ├── diagnostico.py       # resumo mostrado no terminal ao ligar
│   ├── core/                # regras do jogo, sem Discord
│   │   ├── motor.py         # Sessao: pontos, opções ocultas, resultado
│   │   └── carregador.py    # lê e valida os JSON de data/ (item 1)
│   ├── ui/                  # tudo o que o jogador vê
│   │   ├── embeds.py        # fábrica de embeds com temas (item 2)
│   │   └── views.py         # botões da roda de diálogo
│   ├── services/            # coisas que falam com o mundo de fora
│   │   ├── tts.py           # voz: gera o áudio e fala no canal de voz
│   │   └── avatares.py      # acha a foto de cada NPC
│   └── cogs/                # comandos, um tema por arquivo
│       ├── dialogos.py      # !<id>, !falar, !conversas, !recarregar
│       ├── voz.py           # !vozes, !testarvoz
│       └── erros.py         # mensagens amigáveis de erro
├── data/                    # o conteúdo do jogo (você edita aqui)
│   ├── temas.json           # cores e ícones dos embeds
│   ├── npcs/                # um JSON por NPC
│   │   ├── deuzebio.json
│   │   ├── stefano.json
│   │   └── sobrevivente.json
│   ├── story/               # um JSON por história/narração
│   │   └── prologo.json
│   └── schema/              # esquemas que ajudam o VS Code a validar os JSON
├── assets/
│   ├── imagens/             # fotos de perfil dos NPCs
│   └── audio/               # reservada para os itens 7 e 8
└── tests/                   # testes automáticos
```

### Como as peças se encaixam

1. `main.py` lê o `.env` (`config.py`), carrega e valida os JSON (`carregador.py`) e liga o `BillyBot`.
2. O `BillyBot` carrega os cogs. O cog `dialogos` cria um comando para cada JSON.
3. Ao digitar `!deuzebio @jogador`, o cog publica a primeira carta (embed de `embeds.py`) com os botões de `views.py`.
4. Cada clique passa pelas regras de `motor.py` e a carta seguinte aparece no mesmo cartão.
5. Se a voz estiver ligada, `tts.py` fala só a `fala` de cada carta.

**Regra de ouro:** o que é regra do jogo fica em `core/`, o que é visual em `ui/`, o que é comando em `cogs/` e o que é texto da história em `data/`.

### Onde entram os próximos sistemas

| Item | Onde vai morar |
|---|---|
| 3. Ficha e inventário (`/sheet`) | `billybot/cogs/ficha.py` e `billybot/services/banco.py` (SQLite) |
| 4. Memória de escolhas | `billybot/services/banco.py` e um gancho em `core/motor.py` |
| 5. Humor e emoções | `core/motor.py` (o campo `humor` dos JSON já existe) |
| 6. Diário em Markdown | `billybot/cogs/diario.py` |
| 7. Blip-TTS | `billybot/services/blips.py` e `assets/audio/blips/` |
| 8. Trilha por local | `billybot/cogs/ambiente.py` e `assets/audio/ambiente/` |
| 9. Dashboard Flask | pasta `dashboard/` na raiz, lendo o mesmo SQLite |


## Requisitos


- Python 3.9 ou superior
- Uma conta no Discord com permissão para criar bots
- Só para a voz TTS: FFmpeg instalado e internet (a voz usa o `edge-tts`, que acessa
  as vozes neurais da Microsoft sem precisar de chave)
- Para rodar os testes: `python -m pip install -r requirements-dev.txt`

## Passo a passo: colocando para rodar


### 1. Criar o bot no Discord

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications) e crie uma **New Application**.
2. Na aba **Bot**, clique em **Reset Token** e copie o token.
3. Ainda em **Bot**, ative **Message Content Intent** (em *Privileged Gateway Intents*).
4. Em **OAuth2 → URL Generator**, marque o escopo `bot` e as permissões:
   View Channels, Send Messages, Embed Links, Attach Files e Read Message History.
   Para a voz TTS, o bot também precisa de Connect e Speak no canal de voz.
5. Abra a URL gerada e adicione o bot ao seu servidor.

### 2. Preparar o canal de comandos

1. No Discord, ative o **Modo Desenvolvedor** (Configurações → Avançado).
2. Crie o canal onde **você, mestre,** digitará os comandos.
3. Clique com o botão direito no canal e escolha **Copiar ID do canal**.
4. Copie também o ID do canal do RPG, onde os jogadores conversam. O bot precisa
   de permissão para ver e escrever nesse canal.

### 3. Instalar o projeto

```bash
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
python -m pip install -r requirements.txt
```

### 4. Configurar o `.env`

Copie `.env.example` para `.env` (na raiz do projeto, ao lado do `main.py`) e preencha:

```
DISCORD_BOT_TOKEN=seu_token_aqui
CANAL_COMANDOS_ID=id_do_canal_de_comandos
CANAL_RPG_ID=id_do_canal_do_rpg
VOZ_CANAL_ID=id_do_canal_de_voz
FFMPEG_PATH=ffmpeg
```

Se `CANAL_COMANDOS_ID` for `0`, o bot aceita comandos em qualquer canal.
Se `CANAL_RPG_ID` for `0`, a conversa aparece no mesmo canal do comando.
Se `VOZ_CANAL_ID` for `0`, a voz fica desligada. `FFMPEG_PATH` só precisa mudar se o
FFmpeg não estiver no PATH do sistema.

### 5. Ligar o bot

```bash
python main.py
```

Se aparecer `Bot online como ...`, está funcionando.

## Comandos

| Comando | O que faz |
|---|---|
| `!conversas` | Lista as conversas disponíveis, separadas em NPCs e histórias |
| `!falar <id> [@jogador]` | Inicia uma conversa pelo id |
| `!deuzebio [@jogador]` | Encontro com o velho Deuzébio Barbosa, no portão do Subsolo 57 |
| `!stefano [@jogador]` | Conversa com Stefano Sero |
| `!sobrevivente [@jogador]` | Conversa com o Sobrevivente Errante |
| `!prologo [@jogador]` | Prólogo: o despertar da criogenia até o portão |
| `!recarregar` | Relê os JSON de `data/` sem reiniciar o bot |
| `!vozes` | Lista as vozes TTS disponíveis em português do Brasil |
| `!testarvoz <id>` | Fala a primeira fala de um NPC no canal de voz, para ajustar a voz |
| `!help` | Lista os comandos do bot |

O `[@jogador]` é opcional. Marcando um jogador, o nome dele entra nas falas e só
ele pode clicar nos botões. Sem marcar, o nome nas falas vira "viajante" e qualquer
pessoa do canal pode responder.

Cada novo JSON em `data/npcs/` ou `data/story/` ganha o seu comando automaticamente
(use `!recarregar` ou reinicie o bot). Se o id coincidir com um comando do bot
(`help`, `conversas`, `recarregar`, `falar`, `vozes`, `testarvoz`), o bot recusa o arquivo e avisa.

## Como criar uma nova conversa

1. Copie um arquivo existente de `data/npcs/` (para NPCs) ou `data/story/` (para histórias)
   e dê a ele um nome novo, por exemplo `mercador.json`. O nome do arquivo vira o comando `!mercador`.
2. Troque `npc`, `descricao`, `tema`, `voz` e os `nos` (as falas).
3. Em cada opção, `proximo` aponta para outro nó; `null` encerra a conversa.
4. Um nó com `"opcoes": []` é um nó final.
5. Salve e digite `!recarregar` no canal de comandos. Se algo estiver errado, o bot diz o arquivo,
   a linha e a coluna do erro e **mantém a versão anterior funcionando**.

Exemplo mínimo:

```json
{
  "$schema": "../schema/conversa.schema.json",
  "npc": "Mercador Ambulante",
  "descricao": "Falar com o mercador da estrada.",
  "tema": "seguro",
  "voz": { "nome": "pt-BR-AntonioNeural", "velocidade": "+0%", "tom": "+0Hz" },
  "humor": { "confianca": 30 },
  "inicio": "saudacao",
  "nos": {
    "saudacao": {
      "narracao": "Um homem de carroça levanta a mão em cumprimento.",
      "fala": "Boa tarde, {jogador}. Procurando algo?",
      "opcoes": [
        { "texto": "Só olhando.", "proximo": null }
      ]
    }
  }
}
```

A linha `"$schema"` faz o VS Code sublinhar erros e sugerir campos enquanto você digita.

### Cuidados ao editar JSON

- Use sempre aspas duplas (`"`), nunca simples.
- Não deixe vírgula depois do último item de uma lista ou objeto.
- Use `null` (e não `None`), `true` e `false` (em minúsculas).
- JSON não aceita comentários.
- Cores no formato `#RRGGBB`.
- Dentro do texto, use `\n` para quebra de linha e `\"` para aspas.

### Campos de uma conversa

| Campo | Para que serve |
|---|---|
| `id` | Opcional. Nome do comando. Sem ele, vale o nome do arquivo |
| `npc` | Nome do NPC, mostrado ao lado da foto |
| `descricao` | Texto da lista do `!conversas` |
| `tema` | Tema visual de `data/temas.json` |
| `cor` | Opcional. Cor própria no lugar da cor do tema |
| `avatar` | Foto do NPC (veja "Foto de perfil dos NPCs") |
| `voz` | Liga e configura a voz do NPC (veja "Voz dos NPCs (TTS)") |
| `humor` | Valores iniciais de humor do NPC. Já são lidos, e o item 5 vai usá-los |
| `variaveis` | Valores usados nos textos como `{chave}` (ex.: `{codigo_cofre}`) |
| `pontuacao` | Liga o sistema de abordagens |
| `inicio` | Nome do primeiro nó |
| `nos` | Todas as cartas da conversa |

### Campos de um nó

| Campo | Para que serve |
|---|---|
| `tema` | Opcional. Muda a cor e o ambiente só nesta carta |
| `narracao` | Descrição da cena, em itálico. O TTS não fala |
| `fala` | O que o NPC diz, em citação. É só isto que o TTS fala |
| `fala_tts` | Opcional. Mesma fala escrita como se fala, só para a voz (pronúncia) |
| `narracao_final` | Cena que aparece depois da fala |
| `itens` | Itens que o jogador recebe, mostrados em "Itens obtidos" |
| `opcoes` | Botões de resposta do jogador |

### Campos de uma opção

| Campo | Para que serve |
|---|---|
| `texto` | Texto do botão (máximo 80 caracteres) |
| `proximo` | Nó seguinte, `null` para encerrar ou `"@resultado"` para decidir pelos pontos |
| `reacao` | Narração curta que abre o próximo nó |
| `abordagem` | Soma 1 ponto em uma categoria (ex.: `"pacifica"`) |
| `uma_vez` | O botão some depois de usado |

Use `{jogador}` dentro de uma fala para inserir o nome de quem está conversando.

## Sistema de abordagens e diálogo secreto

Em uma conversa com `pontuacao`, cada opção com `abordagem` soma 1 ponto. Quando o
jogador escolhe uma opção com `"proximo": "@resultado"`, vence a categoria com mais
pontos. Em caso de empate no topo, vale a categoria definida em `empate`
(na conversa do Deuzébio, a versão normal).

```json
"pontuacao": {
  "empate": "normal",
  "destinos": {
    "pacifica": "final_pacifica",
    "normal": "final_normal",
    "agressiva": "final_agressiva"
  }
}
```

### Conversa `deuzebio` (`data/npcs/deuzebio.json`)

- 5 cartas (`carta1` a `carta5`). Em cada uma há uma resposta pacífica, uma normal e
  uma agressiva, em posições variadas, sem rótulo.
- A carta 3 tem uma opção extra: `???`, marcada com `"uma_vez": true`.
  - Mostra 3 palavras para dizer. A certa é **Paraíso**, e leva ao diálogo secreto
    (`segredo_1` e `segredo_2`).
  - Se a palavra estiver errada, Deuzébio responde que não entendeu, a conversa volta
    à carta 3 e a opção `???` desaparece.
- Finais: `final_pacifica`, `final_normal`, `final_agressiva` e `segredo_2`.
- O código do cofre fica em `variaveis` (`codigo_cofre`) no JSON.
  O valor atual (`5730`) é provisório: troque pelo código real.

Ao terminar, o bot manda no canal de comandos o caminho percorrido, o placar e o humor.
Isso só acontece quando a conversa é publicada em um canal diferente do canal de comandos.

## Foto de perfil dos NPCs

Cada fala do NPC aparece com a foto de perfil redonda ao lado do nome, como num chat.

### Como adicionar a foto

1. Coloque a imagem na pasta `assets/imagens/`.
2. Ligue a foto ao NPC de um destes jeitos:
   - Nome do arquivo igual ao id da conversa: `deuzebio.png`, `stefano.jpg`, `sobrevivente.webp`; ou
   - Campo `avatar` no JSON, com o caminho a partir da raiz do projeto.
3. Reinicie o bot. Ao ligar, ele lista no terminal quais NPCs têm foto e quais não têm.

Formatos aceitos: png, jpg, jpeg, webp e gif. Use imagens quadradas (de 256x256 a 512x512)
e com menos de 1 MB.

### Outras formas de definir a foto

O campo `avatar` tem prioridade sobre a pasta:

```json
"avatar": "https://exemplo.com/deuzebio.png",
"avatar": "assets/imagens/Deuzébio Babosa.png"
```

Use sempre `/` nos caminhos, mesmo no Windows.

Fotos configuradas hoje:

| Conversa | Arquivo |
|---|---|
| `stefano` | `assets/imagens/Stefano Sero.png` |
| `deuzebio` | `assets/imagens/Deuzébio Babosa.png` |

Sem foto, o NPC continua aparecendo só com o nome em destaque.
O campo `imagem` continua existindo e mostra uma miniatura maior no canto do cartão.

## Temas visuais dos embeds

Todos os embeds do bot saem de `billybot/ui/embeds.py` e usam as cores e os ícones de
`data/temas.json`. Cada conversa escolhe um tema, e cada carta pode trocar de tema.

| Tema | Cor | Para que serve |
|---|---|---|
| `criogenia` | azul estéril | laboratório criogênico |
| `alerta` | vermelho | radiação, fungos e perigo |
| `seguro` | verde | áreas seguras |
| `padrao` | cinza | quando nenhum tema é escolhido |
| `info`, `sucesso`, `erro` | azul, verde, vermelho | mensagens do próprio bot |

### Como o visual é montado

- A **narração** aparece em itálico e a **fala** do NPC em citação (`>`).
- O rodapé mostra o ambiente (ícone e nome do tema) e com quem é a conversa.
- A cor segue esta ordem: `cor` da carta, tema da carta, `cor` da conversa, tema da conversa, `padrao`.
- Exemplo: o Deuzébio é `criogenia` (azul), mas a `carta4` (o estalo metálico) é `alerta` (vermelho)
  e o `final_pacifica` é `seguro` (verde).

### Criar ou mudar um tema

Edite `data/temas.json` e use `!recarregar`:

```json
"laboratorio": { "nome": "Laboratório", "icone": "🧪", "cor": "#9B5DE5" }
```

Depois use `"tema": "laboratorio"` na conversa ou em uma carta. Todo tema precisa de `cor`
(`#RRGGBB`); `nome` e `icone` são opcionais. O tema `padrao` é obrigatório.

## Voz dos NPCs (TTS)

O bot entra no canal de voz quando a conversa é publicada, fala a `fala` de cada carta e
sai quando a conversa termina. Cada NPC pode ter uma voz própria. Tudo isso fica
desligado até você configurar o `VOZ_CANAL_ID`.

### O que é falado

- Só o campo `fala`. A `narracao`, a `reacao`, a `narracao_final` e os itens **nunca** são falados.
- Carta sem `fala` (como a carta `codigo`, do `???`) fica em silêncio.
- Se o jogador clicar rápido, a fala nova interrompe a anterior.
- Clicar em "Encerrar" não repete a fala.
- Valores só de números, como o `{codigo_cofre}`, são falados um dígito por vez
  ("5, 7, 3, 0"). No texto escrito continuam como `5730`.
- Se uma palavra sair mal pronunciada, escreva `fala_tts` na carta com a grafia que soe
  melhor. A voz usa `fala_tts` no lugar de `fala`; o texto na tela não muda.

### Como ligar

1. Instale o FFmpeg. No Windows: `winget install Gyan.FFmpeg`. Feche e abra o terminal
   e confira com `ffmpeg -version`.
2. Rode `python -m pip install -r requirements.txt` (instala `discord.py[voice]` e `edge-tts`).
3. Dê ao bot as permissões **Connect** e **Speak** no canal de voz.
4. Copie o ID do canal de voz e coloque em `VOZ_CANAL_ID` no `.env`.
5. Reinicie o bot. O terminal mostra "Voz TTS ligada. NPCs com voz: ...".
6. Entre no canal de voz com os jogadores e teste com `!testarvoz deuzebio`.

### Escolhendo e ajustando a voz

Cada JSON tem um bloco opcional `voz`. Sem ele, o NPC não fala.

```json
"voz": {
  "nome": "pt-BR-AntonioNeural",
  "velocidade": "-22%",
  "tom": "-12Hz"
}
```

Use `!vozes` para ver os nomes disponíveis. `velocidade` e `tom` são opcionais:
valores negativos deixam a voz mais lenta e mais grave (bom para um velho cansado) e
valores positivos deixam mais rápida e mais aguda. Depois de mudar, use `!recarregar` e
`!testarvoz <id>` até gostar do resultado.

### Como funciona

- Várias conversas ao mesmo tempo: o bot fica no canal até todas terminarem, mas fala uma
  coisa por vez (a mais recente interrompe a anterior).
- Ao terminar a última conversa, o bot espera acabar de falar e sai do canal.
- Os áudios são temporários e apagados logo depois de tocar.
- O `edge-tts` usa um serviço online da Microsoft que não é oferecido como API oficial.
  Ele pode mudar ou ficar fora do ar. Se isso acontecer, o diálogo por texto continua
  funcionando normalmente.

## Solução de problemas


### `LoginFailure: Improper token has been passed` (401 Unauthorized)

O Discord recusou o token. Confira:

1. O token é o da aba **Bot** (botão **Reset Token**), e não o *Application ID*,
   a *Public Key* ou o *Client Secret*.
2. O token aparece só uma vez. Se você clicou em **Reset Token** de novo,
   o anterior deixou de valer.
3. No `.env`, a linha deve ser `DISCORD_BOT_TOKEN=seu_token` sem aspas,
   sem espaços e sem a palavra `Bot`.
4. O arquivo se chama `.env` (e não `.env.txt`) e está na raiz do projeto, na mesma pasta do `main.py`.
   No Windows, ative "Extensões de nomes de arquivos" para conferir.
5. Se o token já foi publicado em algum lugar (GitHub, print, chat), o Discord
   pode tê-lo invalidado. Gere um novo.
6. Uma variável de ambiente `DISCORD_BOT_TOKEN` antiga no Windows pode estar
   sendo usada no lugar do `.env`. Desde a versão 1.0.2 o `.env` tem prioridade.
   Para conferir no PowerShell: `$env:DISCORD_BOT_TOKEN`. Para limpar na sessão:
   `Remove-Item Env:DISCORD_BOT_TOKEN`.
7. Quando o erro aparece, o bot mostra qual `.env` foi lido e o formato do token
   (tamanho e quantidade de pontos), sem exibir o token.

### O editor mostra "Não foi possível resolver a importação "edge_tts""

Esse aviso vem do editor (VS Code/Pylance), não do bot. Ele significa que o editor está
usando um Python diferente daquele onde o pacote foi instalado. Isso é comum no Windows,
principalmente com o Python da Microsoft Store, porque o `pip` solto pode pertencer a
outra versão do Python.

1. Descubra qual Python roda o bot: `python -c "import sys; print(sys.executable)"`.
2. Instale com esse mesmo Python, na pasta do projeto:
   `python -m pip install -r requirements.txt`.
3. Confira: `python -c "import edge_tts; print(edge_tts.__file__)"`. Se imprimir um
   caminho, o pacote está instalado e o bot vai funcionar, mesmo que o editor reclame.
4. No VS Code, aperte `Ctrl+Shift+P`, escolha **Python: Select Interpreter** e selecione o
   mesmo Python do passo 1 (ou o `venv\Scripts\python.exe`, se você usa venv).
5. Aperte `Ctrl+Shift+P` de novo e escolha **Developer: Reload Window**.
6. Com a voz ligada, o bot avisa no terminal se não encontrar `edge-tts` ou `PyNaCl`,
   mostrando o Python em uso e o comando exato para instalar.

### A voz não toca

1. Olhe o terminal: erros de voz começam com `[TTS]` e dizem o motivo.
2. FFmpeg: ao ligar, o bot avisa se não encontrou. Teste `ffmpeg -version` no terminal ou
   coloque o caminho completo em `FFMPEG_PATH`.
3. Confira se o bot tem **Connect** e **Speak** no canal de voz.
4. `VOZ_CANAL_ID` precisa ser o ID de um canal de **voz** (não de texto nem de palco).
5. Se aparecer erro sobre `PyNaCl` ou `edge-tts`, rode `python -m pip install -r requirements.txt` de novo
   (veja também o item abaixo sobre o aviso do editor).
6. A geração da voz precisa de internet.
7. Use `!testarvoz <comando>` para testar sem abrir uma conversa. O NPC precisa ter o bloco `voz`.

### A foto de perfil do NPC não aparece

1. Confira se o arquivo está em `assets/imagens/` e se o nome é igual ao comando
   (`deuzebio.png`, e não `Deuzebio.png.png`). Ative "Extensões de nomes de
   arquivos" no Windows para conferir.
2. Ao ligar o bot, veja no terminal a linha "NPCs com foto".
3. Com o campo `avatar`, confira se o caminho ou o link está certo. O bot avisa
   no terminal quando não encontra o arquivo.
4. O bot precisa da permissão **Attach Files** no canal do RPG para enviar a foto.

### O bot não liga e mostra "Erros encontrados nos arquivos de data/"

Cada erro diz o arquivo e o lugar do problema, por exemplo
`[npcs/deuzebio.json] JSON inválido na linha 42, coluna 7`. Os motivos mais comuns são
vírgula sobrando ou faltando, aspas simples no lugar de duplas, um `proximo` que aponta para um
nó que não existe e um `tema` que não está em `temas.json`. Corrija e rode de novo.

### Criei um JSON novo e o comando não aparece

1. Digite `!recarregar` no canal de comandos (ou reinicie o bot).
2. Se o bot responder "Nada foi recarregado", leia o erro: nada muda enquanto houver um JSON quebrado.
3. O id não pode ser `help`, `conversas`, `recarregar`, `falar`, `vozes` nem `testarvoz`,
   e só pode ter letras minúsculas, números e `_`.

### O bot mostra "Aviso: nós de onde a conversa nunca consegue terminar"

Não é um erro, mas indica que existe uma carta da qual o jogador só consegue voltar para trás
e nunca chega a um final. Dê a ela uma opção com `"proximo": null` ou que leve a um nó final.

### O comando funciona, mas a conversa não aparece no canal do RPG

Confira o `CANAL_RPG_ID` no `.env` e se o bot tem permissão para ver e escrever
nesse canal (View Channels, Send Messages e Embed Links).

## Próximas atualizações

Roteiro das melhorias planejadas, em ordem de complexidade.

| # | Melhoria | Situação |
|---|---|---|
| 1 | Diálogos e fichas de NPC em JSON (`data/npcs/` e `data/story/`) | Pronto na 2.0.0 |
| 2 | Embeds dinâmicos com temas visuais | Pronto na 2.0.0 |
| 3 | Ficha de personagem e inventário com `/sheet` (SQLite) | Planejada |
| 4 | Memória de escolhas (histórico de nós e escolhas críticas) | Planejada |
| 5 | Humor e emoções dinâmicas (variáveis de estado que liberam opções) | Planejada |
| 6 | Diário de sessão exportável em Markdown | Planejada |
| 7 | Blip-TTS no estilo Undertale/Deltarune | Planejada |
| 8 | Trilha sonora dinâmica por local, no canal de voz | Planejada |
| 9 | Dashboard web de administração (Flask) | Planejada |

A ideia de usar atributos da ficha nas conversas (por exemplo, negociar um pedágio conforme o
Carisma) volta junto com os itens 3 e 5. A ideia de bots de NPC separados continua anotada para depois.

## Histórico de alterações

### [2.0.0] – 2026-11-12

- Projeto reorganizado em pacote `billybot/` com **cogs**: `dialogos`, `voz` e `erros`.
  Novo ponto de entrada: `python main.py`. Os arquivos `bot.py`, `conversas.py`, `motor.py`
  e `tts.py` da raiz deixam de existir (o conteúdo foi para `billybot/`).
- Item 1: textos das conversas movidos para JSON em `data/npcs/` e `data/story/`. Os NPCs
  `deuzebio`, `stefano` e `sobrevivente` foram migrados sem mudar as falas.
- Item 1: novo arquivo `data/story/prologo.json` com o prólogo do Subsolo 57 (`!prologo`).
- Item 1: o campo `humor` (valores iniciais) já é lido dos JSON e aparece no relatório do mestre.
- Item 1: carregador com validação e mensagens com arquivo, linha e coluna; avisos de nós
  inalcançáveis e de nós sem saída; esquemas JSON em `data/schema/` para o VS Code.
- Item 2: embeds padronizados em `billybot/ui/embeds.py`, com temas em `data/temas.json`
  (`criogenia`, `alerta`, `seguro`, `info`, `sucesso`, `erro`). A cor pode mudar a cada carta.
- Item 2: fala do NPC em citação e narração em itálico; rodapé com o ambiente atual.
- Item 2: todas as mensagens do bot (erros, listas, confirmações) agora são embeds.
- Novos comandos: `!falar <id> [@jogador]` e `!recarregar` (relê os JSON sem reiniciar).
- Fotos movidas para `assets/imagens/`. O campo `avatar` agora usa esse caminho.
- Configuração agora lida por `billybot/config.py`, sempre do `.env` na raiz do projeto.
- Suíte de testes com pytest (59 testes) e `requirements-dev.txt`.
- As cores antigas por conversa foram trocadas pelas cores dos temas.
- Incorporadas as melhorias da versão 1.3.1 (aviso de `edge-tts`/`PyNaCl` ausentes ao ligar).


### [1.3.1] – 2026-10-31

- Com a voz ligada, o bot confere no início se `edge-tts` e `PyNaCl` estão instalados no
  Python em uso e, se não estiverem, mostra o Python e o comando exato para instalar.
- A mensagem de erro do `edge-tts` ausente também mostra o Python em uso.
- Instalação padronizada com `python -m pip install -r requirements.txt`, para garantir
  que o pacote vá para o mesmo Python que roda o bot.
- Novo item em "Solução de problemas" sobre o aviso do editor (Pylance).

### [1.3.0] – 2026-10-31

- Voz TTS: o bot fala em um canal de voz apenas o campo `fala` de cada carta, sem ler a narração.
- Novo módulo `tts.py` (geração do áudio com `edge-tts` e reprodução com FFmpeg).
- Novo bloco opcional `voz` por conversa (nome da voz, velocidade e tom) e novo campo
  opcional `fala_tts` por carta (pronúncia).
- Vozes configuradas para `stefano`, `sobrevivente` e `deuzebio`.
- Novos comandos: `!vozes` (lista as vozes) e `!testarvoz <comando>` (testa a voz de um NPC).
- Números como o código do cofre são falados um dígito por vez.
- Novas variáveis no `.env`: `VOZ_CANAL_ID` (0 = voz desligada) e `FFMPEG_PATH`.
- Novas dependências: `discord.py[voice]` e `edge-tts`. Novas permissões do bot no canal de voz: Connect e Speak.
- A validação das conversas agora confere o formato de `velocidade` e `tom`.
- O README ganhou as seções "Voz dos NPCs (TTS)" e o item "A voz não toca" em "Solução de problemas".

### [1.2.1] – 2026-10-31

- Configuradas as fotos de perfil de Stefano Sero (`imagens/Stefano Sero.png`) e de
  Deuzébio (`imagens/Deuzébio Babosa.png`) pelo campo `avatar` em `conversas.py`.

### [1.2.0] – 2026-10-31

- Foto de perfil de cada NPC ao lado do nome em todas as falas.
- A foto é procurada automaticamente em `imagens/<comando>.png` (ou jpg, jpeg, webp, gif),
  ou definida pelo novo campo opcional `avatar` (link ou caminho de arquivo).
- Ao ligar, o bot lista no terminal quais NPCs têm foto e avisa se um `avatar` não existe.
- Sem foto, o visual continua o mesmo de antes.
- Nova permissão necessária no canal do RPG: Attach Files.
- Seção "Solução de problemas" ganhou o item sobre a foto do NPC.

### [1.1.0] – 2026-10-30

- O mestre agora digita o comando no canal de comandos e a conversa é publicada no
  canal do RPG (novo `CANAL_RPG_ID` no `.env`).
- Os comandos aceitam `[@jogador]`: marcando, só aquele jogador responde; sem marcar,
  qualquer pessoa do canal pode responder.
- Criado `motor.py` com as regras da conversa, separadas do Discord.
- Novo sistema de abordagens por pontos (`abordagem`, `pontuacao`, `@resultado`),
  com desempate para a versão normal.
- Novas opções de conversa: `uma_vez`, `reacao`, `narracao`, `narracao_final`,
  `itens` e `variaveis`.
- Texto das conversas separado em narração e fala (preparação para o TTS).
- Relatório para o mestre ao fim da conversa (caminho e placar).
- Nova conversa `deuzebio`, com 5 cartas, 3 finais e diálogo secreto.
- As conversas `stefano` e `sobrevivente` tiveram a narração separada da fala,
  sem mudar o texto que o jogador vê.
- A validação das conversas agora confere abordagens, variáveis e nós sem texto.
- Seção "Solução de problemas" ganhou o item sobre o canal do RPG.

### [1.0.2] – 2026-10-30

- O `.env` agora tem prioridade sobre variáveis de ambiente do sistema (`override=True`).
- Em caso de token recusado, o bot mostra o `.env` usado e o formato do token.
- Seção "Solução de problemas" atualizada.

### [1.0.1] – 2026-10-30

- O bot agora mostra uma mensagem clara quando o Discord recusa o token.
- Adicionada a seção "Solução de problemas" ao README.

### [1.0.0] – 2026-10-28

- Removida a integração com a API da OpenAI (`openai`, `ask_gpt`, `buscar_historico_canal`).
- Bot reescrito como chatbot comum, baseado em comandos e diálogos por botões.
- Criado `conversas.py` com duas conversas de exemplo (`stefano` e `sobrevivente`).
- Adicionada restrição ao canal de comandos via `CANAL_COMANDOS_ID`.
- Adicionada validação das conversas ao iniciar o bot.
- Corrigidos problemas do código original: `intents.message` (o correto é
  `message_content`), vírgulas faltando em dicionários e chamadas, `f-string`
  ausente na mensagem de inicialização.
