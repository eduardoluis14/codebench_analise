import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

def calcular_numero_de_testes(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário: {id_exercicio: {id_aluno: total_testes}}
    dados_testes = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum ficheiro .log encontrado. Verifique o caminho.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M4 - Número de Testes"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_testes:
            dados_testes[exercicio_id] = {}
        
        if aluno_id not in dados_testes[exercicio_id]:
            dados_testes[exercicio_id][aluno_id] = 0

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    
                    if evento.get('eventType') == 'run':
                        dados_testes[exercicio_id][aluno_id] += 1
                            
        except Exception:
            continue

    # Gerar o relatório de médias
    relatorio = []
    for ex_id, alunos_dict in dados_testes.items():
        valores = list(alunos_dict.values())
        
        # Filtro: Contar apenas os alunos que efetivamente usaram o botão "Run"
        # Isso remove da média alunos que apenas abriram a aba ou submeteram sem testar
        valores_validos = [v for v in valores if v > 0]
        total_alunos_validos = len(valores_validos)
        
        # Significância Estatística
        if total_alunos_validos >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos, ddof=1)
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': total_alunos_validos,
                'Total_Execucoes_Run': sum(valores_validos),
                'Media_Testes_M4': round(media, 2),
                'Mediana_Testes_M4': round(mediana, 2),
                'Desvio_Padrao_M4': round(desvio_padrao, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com testes realizados.")
        return

    df = pd.DataFrame(relatorio)
    # Ordenamos pela Mediana para isolar alunos que testam centenas de vezes compulsivamente
    df = df.sort_values(by='Mediana_Testes_M4', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M4 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_numero_de_testes(path_t)
