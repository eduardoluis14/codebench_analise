import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

def calcular_esforco_submissoes_sucesso(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    dados_esforco = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))

    if not arquivos:
        print("Nenhum ficheiro .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M2 - Esforço até Sucesso"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_esforco:
            dados_esforco[exercicio_id] = {}
        
        if aluno_id not in dados_esforco[exercicio_id]:
            dados_esforco[exercicio_id][aluno_id] = {'submissoes': 0, 'sucesso': False}

        try:
            eventos = []
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    try:
                        eventos.append(json.loads(linha))
                    except json.JSONDecodeError:
                        continue
            
            try:
                eventos.sort(key=lambda x: datetime.fromisoformat(x.get('dateTime', '').replace('Z', '+00:00')))
            except Exception:
                eventos.sort(key=lambda x: x.get('dateTime', ''))
            
            for evento in eventos:
                if evento.get('eventType') == 'submission':
                    dados_esforco[exercicio_id][aluno_id]['submissoes'] += 1
                    
                    detalhes = evento.get('details', {})
                    try:
                        correctness = float(detalhes.get('correctness', 0))
                    except (ValueError, TypeError):
                        correctness = 0.0

                    if correctness == 1.0:
                        dados_esforco[exercicio_id][aluno_id]['sucesso'] = True
                        break # Para de ler eventos deste aluno para este exercício, pois já acertou!
                        
        except Exception:
            continue

    # Agregação e estatísticas básicas necessárias para o output final
    relatorio = []
    for ex_id, alunos_dict in dados_esforco.items():
        valores_validos = [v['submissoes'] for v in alunos_dict.values() if v['sucesso']]
        total_alunos_tentaram = len([v for v in alunos_dict.values() if v['submissoes'] > 0])
        total_alunos_sucesso = len(valores_validos)
        
        if total_alunos_sucesso >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos, ddof=1)
            
            q1 = np.percentile(valores_validos, 25)
            q3 = np.percentile(valores_validos, 75)
            iqr = q3 - q1
            
            taxa_resolucao = (total_alunos_sucesso / total_alunos_tentaram) * 100 if total_alunos_tentaram > 0 else 0
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Tentaram': total_alunos_tentaram,
                'Qtd_Alunos_Sucesso': total_alunos_sucesso,
                'Taxa_Resolucao_%': round(taxa_resolucao, 2),
                'Media_Submissoes_M2': round(media, 2),
                'Mediana_Submissoes_M2': round(mediana, 2),
                'Desvio_Padrao_M2': round(desvio_padrao, 2),
                'Q1_M2': round(q1, 2),
                'Q3_M2': round(q3, 2),
                'IQR_M2': round(iqr, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com sucesso.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Mediana_Submissoes_M2', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_esforco_submissoes_sucesso(path_t)
