import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

def calcular_numero_de_consultas(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário: {id_exercicio: {id_aluno: total_consultas}}
    dados_consultas = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum ficheiro .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M5 - Número de Consultas"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_consultas:
            dados_consultas[exercicio_id] = {}
        
        if aluno_id not in dados_consultas[exercicio_id]:
            dados_consultas[exercicio_id][aluno_id] = 0

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    
                    # M5: Somatório entre submissões e testes
                    if evento.get('eventType') in ['submission', 'run']:
                        dados_consultas[exercicio_id][aluno_id] += 1
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, alunos_dict in dados_consultas.items():
        valores = list(alunos_dict.values())
        
        # Filtro: Contar apenas alunos que efetivamente fizeram pelo menos 1 consulta (run ou submission)
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
                'Total_Soma_Submissoes_e_Testes': sum(valores_validos),
                'Media_Consultas_M5': round(media, 2),
                'Mediana_Consultas_M5': round(mediana, 2),
                'Desvio_Padrao_M5': round(desvio_padrao, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com consultas realizadas.")
        return

    df = pd.DataFrame(relatorio)
    # Ordenar pela Mediana (mais robusta contra alunos que consultam exaustivamente)
    df = df.sort_values(by='Mediana_Consultas_M5', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M5 salvo em: {output_file}")

# Caminho do HD Externo
path_t = 'exemplo/transactions'
calcular_numero_de_consultas(path_t)
