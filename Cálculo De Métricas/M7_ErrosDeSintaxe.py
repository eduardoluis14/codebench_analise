import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def calcular_erros_de_sintaxe(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário: {id_exercicio: {id_aluno: total_erros_sintaxe}}
    dados_sintaxe = {}

    print(f"Lendo logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print(f"Nenhum arquivo .log encontrado em {diretorio_transactions}")
        return

    for arquivo_log in tqdm(arquivos, desc="Analisando M7 - Erros de Sintaxe"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_sintaxe:
            dados_sintaxe[exercicio_id] = {}
        
        if aluno_id not in dados_sintaxe[exercicio_id]:
            dados_sintaxe[exercicio_id][aluno_id] = 0

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    evento = json.loads(linha)
                    
                    # M7: Erros de Sintaxe
                    # Identificado quando há uma submissão, mas o campo 'correctness' está ausente 
                    # ou indica erro fatal de execução (geralmente details vazio ou com erro de traceback)
                    if evento.get('eventType') == 'submission':
                        detalhes = evento.get('details', {})
                        
                        # Se não houver a chave 'correctness' ou se houver indicação de erro de execução
                        if 'correctness' not in detalhes or detalhes.get('correctness') is None:
                            dados_sintaxe[exercicio_id][aluno_id] += 1
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, alunos_dict in dados_sintaxe.items():
        valores_erros = list(alunos_dict.values())
        total_alunos = len(valores_erros)
        
        if total_alunos > 0:
            total_erros_exercicio = sum(valores_erros)
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos': total_alunos,
                'Total_Erros_Sintaxe': total_erros_exercicio,
                'Media_Erros_Sintaxe_M7': round(total_erros_exercicio / total_alunos, 2)
            })

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Media_Erros_Sintaxe_M7', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M7 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_erros_de_sintaxe(path_t)
