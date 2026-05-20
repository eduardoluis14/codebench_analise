import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

def calcular_eventos_de_delecao(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    dados_delecao = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print(f"Nenhum ficheiro .log encontrado em {diretorio_transactions}")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M10 - Deleções"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_delecao:
            dados_delecao[exercicio_id] = {}
        
        if aluno_id not in dados_delecao[exercicio_id]:
            dados_delecao[exercicio_id][aluno_id] = 0

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue 
                    
                    if evento.get('eventType') == 'generic' and 'details' in evento:
                        detalhes = evento.get('details', {})
                        
                        # Garantir que é um diff textual real antes de checar
                        if 'fromA' in detalhes and 'toA' in detalhes:
                            fromA = detalhes.get('fromA')
                            toA = detalhes.get('toA')
                            
                            # Se o limite final (toA) for maior que o inicial (fromA), houve deleção
                            if toA > fromA:
                                dados_delecao[exercicio_id][aluno_id] += 1
                            
        except Exception:
            continue

    relatorio = []
    for ex_id, alunos_dict in dados_delecao.items():
        valores = list(alunos_dict.values())
        
        valores_validos = [v for v in valores if v > 0]
        total_alunos_validos = len(valores_validos)
        
        if total_alunos_validos >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos, ddof=1)
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': total_alunos_validos,
                'Total_Acoes_Delecao': sum(valores_validos),
                'Media_Delecoes_M10': round(media, 2),
                'Mediana_Delecoes_M10': round(mediana, 2),
                'Desvio_Padrao_M10': round(desvio_padrao, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com eventos de deleção.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Mediana_Delecoes_M10', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M10 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_eventos_de_delecao(path_t)
