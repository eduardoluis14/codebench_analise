# Classificador de Padrões e Extrator de Métricas Educacionais

Este repositório contém o pipeline de processamento de dados desenvolvido para o projeto de pesquisa em Mineração de Dados Educacionais. O objetivo deste classificador é mapear a estrutura algorítmica de exercícios de programação e correlacionar estes padrões com métricas de esforço e desempenho discente, utilizando como base logs de interação de um juiz online.

## 1. Catalogação de Padrões (Programming Plans)

O sistema utiliza uma taxonomia baseada em planos de programação, adaptando conceitos da literatura de De Raadt (2008) e Cruz Izu (2021) para a sintaxe Python. Os padrões atuais são:

* **Input-Process-Output (IPO):** Sequência lógica básica de entrada, processamento e saída.
* **Conditional Branching:** Tomada de decisão complexa com caminhos alternativos (`if/else`, `elif`).
* **Initialisation:** Definição de variáveis de controle (acumuladores ou flags) antes de estruturas iterativas.
* **Divisibility:** Testes lógicos envolvendo o operador de módulo (`%`).
* **Number Decomposition:** Fatiamento de dígitos de números inteiros via divisões sucessivas.
* **Min/Max:** Aplicação de funções de extração de extremos.
* **Triangular Swap:** Troca de valores entre variáveis utilizando tuplas.
* **Filter A Collection:** Filtragem de séries de dados.
* **Guarded Exception:** Estruturas de interrupção (return/raise/break) para controle de fluxo.
* **Validate:** Verificação de validade de estados dentro de laços.
* **Indicators:** Utilização de flags booleanas dentro de estruturas condicionais.
* **Delimiting Strings:** Lógica para formatação de saída (ex: junção de strings com delimitadores).
* **MultiCount:** Contagem múltipla utilizando estruturas de dados.
* **Command Line Arguments:** Tratamento de argumentos via terminal.

> **Nota:** Este catálogo encontra-se em fase de validação e está sujeito a refinamentos semânticos em versões futuras, conforme a necessidade de abrangência do currículo da disciplina.

## 2. Cálculo de Métricas (Atrito Cognitivo)

O pipeline processa 13 métricas de esforço derivadas dos logs de submissão e interação:

1. **M1 (Taxa de Acerto):** Percentual de sucesso nas submissões.
2. **M2 (Esforço de Submissão):** Quantidade total de tentativas por exercício.
3. **M3 (Taxa de Aceitação):** Eficiência na conversão de tentativas em acertos.
4. **M4 (Uso de Testes):** Frequência de execução de casos de teste.
5. **M5 (Consultas ao Juiz):** Quantidade de verificações realizadas.
6. **M6 (Erros de Lógica):** Frequência de falhas semânticas na submissão.
7. **M7 (Erros de Sintaxe):** Ocorrências de erros de compilação ou sintaxe.
8. **M8 (Total de Erros):** Acúmulo de falhas totais por estudante/questão.
9. **M9 (Eventos de Interação):** Volume total de microações (teclado/mouse).
10. **M10 (Deleções/Refatoração):** Eventos de exclusão de código no editor.
11. **M11 (Tempo de Implementação):** Duração total da atividade no juiz.
12. **M12 (Frequência de Edição):** Quantidade de alterações realizadas no código.
13. **M13 (Índice de Discriminação):** Poder da questão em distinguir alunos de alto e baixo desempenho.

## 3. Filtragem de Dados (Lista VIP)

Para garantir a qualidade da análise, o pipeline opera estritamente sobre uma "Lista VIP" de exercícios. Esta lista foi gerada a partir do cruzamento entre o repositório total de questões da plataforma e um dataset validado fornecido pela coordenação, contendo exclusivamente **exercícios aplicados em provas oficiais**.

Este filtro garante que a pesquisa foque em dados de alta qualidade e relevância pedagógica, descartando exercícios de fixação, listas de exercícios extracurriculares ou questões de teste que poderiam introduzir ruído estatístico na análise de atrito cognitivo.

## 4. Arquitetura do Classificador

O sistema foi construído com uma arquitetura de duas passagens (*Two-Pass Analysis*):

* **Parte 1:** Extrai métricas estruturais (profundidade, complexidade ciclomática, contagem de laços e condicionais).
* **Parte 2:** Detecta os padrões algorítmicos utilizando o contexto global fornecido pela primeira passagem, reduzindo falsos positivos e permitindo uma modelagem mais próxima da intenção lógica do aluno.
