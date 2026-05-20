import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def calcular_taxa_aceitacao_oj(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário simplificado: rastreia totais e alunos únicos
    stats_aceitacao = {}

    print(f"Lendo logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))

    if not arquivos:
        print("Nenhum arquivo .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="Analisando M3 - Taxa de Aceitação (OJ)"):
        exercicio_id = arquivo_log.stem

        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in stats_aceitacao:
            stats_aceitacao[exercicio_id] = {'corretas': 0, 'total': 0, 'alunos_unicos': set()}

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    
                    if evento.get('eventType') == 'submission':
                        stats_aceitacao[exercicio_id]['alunos_unicos'].add(aluno_id)
                        stats_aceitacao[exercicio_id]['total'] += 1
                        
                        detalhes = evento.get('details', {})
                        
                        try:
                            correctness = float(detalhes.get('correctness', 0))
                        except (ValueError, TypeError):
                            correctness = 0.0

                        if correctness == 1.0:
                            stats_aceitacao[exercicio_id]['corretas'] += 1
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, counts in stats_aceitacao.items():
        qtd_alunos = len(counts['alunos_unicos'])
        total = counts['total']
        corretas = counts['corretas']
        
        # Significância Estatística
        if qtd_alunos >= 16 and total > 0:
            taxa = (corretas / total) * 100
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': qtd_alunos,
                'Submissoes_Totais': total,
                'Submissoes_Corretas': corretas,
                'Taxa_Aceitacao_%_M3': round(taxa, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Taxa_Aceitacao_%_M3', ascending=True)
    
    output_file = "exexmplo/saida.csv"
    df.to_csv(output_file, index=False)
    print(f"\nRelatório M3 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_taxa_aceitacao_oj(path_t)
