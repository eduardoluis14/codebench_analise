# Classificador de Padrões e Extrator de Métricas Educacionais

Este repositório contém o pipeline de processamento de dados desenvolvido para o projeto de pesquisa em Mineração de Dados Educacionais. O objetivo é mapear a estrutura algorítmica de exercícios de programação e correlacionar estes padrões com métricas de esforço e desempenho discente, utilizando logs de interação de um juiz online.

## 1. Estrutura de Dados Necessária

Para que o pipeline de extração funcione corretamente, o diretório raiz do projeto deve conter a seguinte estrutura de dados:

* `transactions/`: Pasta contendo os logs brutos das ações dos alunos. O script espera que os logs estejam organizados em subpastas por `ID_Aluno/ID_Turma/ID_Trabalho/`.
* `exercises/`: Pasta contendo as soluções de referência disponibilizadas pelos docentes. Cada subpasta deve corresponder a um `ID_Exercicio` e conter o arquivo `sample_solution.py` (ou um arquivo de solução de referência).
* `ids_questoes_de_prova_ipc.txt`: Arquivo de texto contendo a lista dos IDs dos exercícios que compõem a "Lista VIP" (questões aplicadas em provas oficiais). O pipeline filtrará os dados baseando-se exclusivamente nestes IDs. O motivo de aplicar este filtro é isolar o escopo da pesquisa, garantindo que a análise de atrito cognitivo seja feita apenas com dados de avaliações reais, descartando ruídos gerados por exercícios de fixação livres. Estes IDs específicos foram extraídos de um arquivo CSV fornecido pelo professor David Fernandes (o arquivo original pode ser encontrado neste repositório dentro da pasta `Data`).

> **Nota:** Solicitar os dados os dados, caso seja necessário, com o professore responsável (David Fernandes).

## 2. Catalogação de Padrões (Programming Plans)

O sistema utiliza uma taxonomia baseada em planos de programação, identificados por meio da análise estática (AST) do gabarito docente. A catalogação inicial abrangeu 11 padrões estruturais. Contudo, para garantir a significância estatística das comparações (seguindo o critério de $N \ge 30$ instâncias por padrão), a análise foi consolidada nos 6 padrões que atingiram o piso amostral mínimo.

**Padrões identificados:**

* **Input-Output Sequencial:** Leitura, processamento e saída sem ramificações. 
* **Condicional Simples:** Uso de estrutura `if` isolada.
* **Condicional Composto:** Uso de estrutura `if/else`. 
* **Condicional Encadeado:** Uso de estrutura `if/elif/else`.
* **Condicional Aninhado:** Estrutura `if` inserida em outro `if`. 
* **Repetição com Condição e Incremento:** Laço contendo `if` com incremento de variável. 
* **Repetição com Condição e Acúmulo:** Laço contendo `if` com acúmulo de variável. 
* **Repetição - Incremento de variável:** Laço simples de contagem.
* **Repetição - Acúmulo de variável:** Laço simples de somatório.
* **Estrutura Linear (Iteração por índice):** Acesso a elementos via índices (`range`, `len`).
* **Estrutura Linear (Iteração por valor):** Acesso direto a elementos da coleção.

> **Nota:** Os padrões marcados como (*Analisado*) compõem o conjunto final de 329 exercícios utilizados nos testes estatísticos de esforço. Os demais padrões foram catalogados, mas descartados da análise inferencial por não atingirem o volume mínimo de dados para conferir robustez estatística aos resultados.

## 3. Cálculo de Métricas (Atrito Cognitivo)

O pipeline processa 13 métricas de esforço derivadas dos logs de submissão e interação:

1. **M1 (Taxa de Acerto):** Percentual de sucesso nas submissões.
2. **M2 (Esforço de Submissão):** Quantidade total de tentativas.
3. **M3 (Taxa de Aceitação):** Eficiência na conversão de tentativas em acertos.
4. **M4 (Uso de Testes):** Frequência de execução de testes.
5. **M5 (Consultas ao Juiz):** Quantidade de verificações.
6. **M6 (Erros de Lógica):** Falhas semânticas na submissão.
7. **M7 (Erros de Sintaxe):** Ocorrências de erros de sintaxe.
8. **M8 (Total de Erros):** Acúmulo de falhas totais.
9. **M9 (Eventos de Interação):** Volume de microações.
10. **M10 (Deleções/Refatoração):** Eventos de exclusão de código.
11. **M11 (Tempo de Implementação):** Duração total da atividade.
12. **M12 (Frequência de Edição):** Alterações realizadas no código.
13. **M13 (Índice de Discriminação):** Poder da questão em distinguir desempenho.

É importante destacar que os scripts calculam essas métricas realizando a leitura de toda a pasta de `transactions` originalmente. A filtragem utilizando apenas os IDs de prova é aplicada em uma etapa posterior, durante a consolidação dos dados. Essa arquitetura foi planejada para permitir que pesquisas futuras possam reaproveitar os mesmos scripts caso precisem calcular e analisar o atrito cognitivo em exercícios comuns e listas de fixação, além das provas oficiais.

## 4. Arquitetura do Classificador

O sistema utiliza uma arquitetura de duas passagens (Two-Pass Analysis):

* **Parte 1:** Extrai métricas estruturais (profundidade, complexidade ciclomática, contagem de laços e condicionais).
* **Parte 2:** Detecta os padrões algorítmicos utilizando o contexto global fornecido pela primeira passagem, garantindo maior precisão na classificação e redução de falsos positivos.

## 5. Estrutura

Como os arquivos brutos de logs e submissões são muito pesados, eles não estão versionados neste repositório.

```text
📁 raiz_do_projeto/
├── 📁 DataSet/
│   ├── 📄 ids_questoes_de_prova_ipc.txt   # (Já incluso no repositório)
│   ├── 📁 exercises/                      # (Coloque a pasta descompactada aqui)
│   │   ├── 📁 1005919218/                 # ID do Exercício
│   │   │   └── 📄 sample_solution.py      # Solução de referência do professor
│   │   └── 📁 ...
│   └── 📁 transactions/                   
│       ├── 📁 3225967263/                 # ID do Aluno
│       │   └── 📁 3573129627/             # ID da Turma
│       │       └── 📁 1407130552/         # ID do Trabalho
│       │           └── 📄 2667036473.log  # ID da questão + Log de keystrokes/submissões
│       └── 📁 ...

```

> **Nota:** Ajuste o caminho dos dados nos scripts caso seja necessário.
