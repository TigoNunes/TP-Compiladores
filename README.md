# TP-Compiladores

Interpretador de bytecode em Python para o trabalho pratico de Compiladores.

## Como executar

Lendo o programa pela entrada padrao:

```bash
python main.py < examples/pdf_01_basic.bytecode
```

Ou passando o arquivo como argumento:

```bash
python main.py examples/pdf_04_while.bytecode
```

Para programas com `READ`, informe os valores de entrada com `--input`:

```bash
python main.py --input "10 20" programa.bytecode
```

## Instrucoes suportadas

- Pilha e aritmetica: `PUSH`, `POP`, `ADD`, `SUB`, `MUL`, `DIV`, `MOD`, `NEG`
- Variaveis: `STORE`, `LOAD`
- Fluxo de controle: `JMP`, `JZ`, `JNZ`, `HALT`
- Comparacao: `EQ`, `NEQ`, `LT`, `GT`, `LE`, `GE`
- Funcoes e E/S: `CALL`, `RET`, `PRINT`, `READ`
- Auxiliares: labels no formato `NOME:` e linhas vazias/comentarios com `#`

Enderecos numericos em `JMP`, `JZ`, `JNZ` e `CALL` seguem o formato do PDF: sao multiplos de 4
e sao convertidos para indice de instrucao com `endereco / 4`. Labels tambem podem ser usados.

## Otimizacao extra

O projeto inclui um otimizador conservador com:

- constant folding
- constant propagation
- remocao de `PUSH` seguido por `POP`
- eliminacao simples de stores mortos

Exemplo:

```bash
python main.py --dump-optimized examples/optimization/example_05.before.bytecode
```

Os 5 exemplos pedidos para a parte extra estao em `examples/optimization`, com pares
`*.before.bytecode` e `*.after.bytecode`.

## Testes

```bash
python -m unittest
```

Os testes cobrem os exemplos do PDF, `READ`, erros de execucao, enderecos numericos e otimizacao.
