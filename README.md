# Classificador de Padrões e Extrator de Métricas Educacionais

Este repositório contém o pipeline de processamento de dados desenvolvido para o projeto de pesquisa em Mineração de Dados Educacionais. O objetivo é mapear a estrutura algorítmica de exercícios de programação e correlacionar estes padrões com métricas de esforço e desempenho discente, utilizando logs de interação de um juiz online.

## 1. Estrutura de Dados Necessária

Para que o pipeline de extração funcione corretamente, o diretório raiz do projeto deve conter a seguinte estrutura de dados:

* `transactions/`: Pasta contendo os logs brutos das ações dos alunos. O script espera que os logs estejam organizados em subpastas por `ID_Aluno/ID_Turma/ID_Trabalho/`.
* `exercises/`: Pasta contendo as soluções de referência disponibilizadas pelos docentes. Cada subpasta deve corresponder a um `ID_Exercicio` e conter o arquivo `sample_solution.py` (ou um arquivo de solução de referência).
* `ids_questoes_de_prova_ipc.txt`: Arquivo de texto contendo a lista dos IDs dos exercícios que compõem a "Lista VIP" (questões aplicadas em provas oficiais). O pipeline filtrará os dados baseando-se exclusivamente nestes IDs.

> **Nota:** Solicitar os dados os dados, caso seja necessário, com o professore responsável (David Fernandes).
 
## 2. Catalogação de Padrões (Programming Plans)

O sistema utiliza uma taxonomia baseada em planos de programação, adaptando conceitos da literatura de De Raadt (2008) e Cruz Izu (2021) para a sintaxe Python. Os padrões atuais são:

* **Input-Process-Output (IPO):** Sequência lógica básica de entrada, processamento e saída.
* **Conditional Branching:** Tomada de decisão complexa com caminhos alternativos (`if/else`, `elif`).
* **Initialisation:** Definição de variáveis de controle antes de estruturas iterativas.
* **Divisibility:** Testes lógicos envolvendo o operador de módulo (`%`).
* **Number Decomposition:** Fatiamento de dígitos de números inteiros via divisões sucessivas.
* **Min/Max:** Aplicação de funções de extração de extremos.
* **Triangular Swap:** Troca de valores entre variáveis.
* **Filter A Collection:** Filtragem de séries de dados.
* **Guarded Exception:** Estruturas de interrupção para controle de fluxo.
* **Validate:** Verificação de validade de estados dentro de laços.
* **Indicators:** Utilização de flags booleanas para controle.
* **Delimiting Strings:** Lógica para formatação de saída.
* **MultiCount:** Contagem múltipla utilizando estruturas de dados.
* **Command Line Arguments:** Tratamento de argumentos via terminal.

> **Nota:** Este catálogo encontra-se em fase de validação e está sujeito a refinamentos semânticos em versões futuras.

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

## 4. Arquitetura do Classificador

O sistema utiliza uma arquitetura de duas passagens (*Two-Pass Analysis*):

* **Parte 1:** Extrai métricas estruturais (profundidade, complexidade ciclomática, contagem de laços e condicionais).
* **Parte 2:** Detecta os padrões algorítmicos utilizando o contexto global fornecido pela primeira passagem, garantindo maior precisão na classificação e redução de falsos positivos.

## 5. Estrutura

Como os arquivos brutos de logs e submissões são muito pesados, eles **não estão versionados neste repositório**. 

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
