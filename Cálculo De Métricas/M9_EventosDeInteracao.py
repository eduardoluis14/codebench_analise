import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

def calcular_eventos_de_interacao(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário: {id_exercicio: {id_aluno: total_eventos}}
    dados_interacao = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print(f"Nenhum ficheiro .log encontrado em {diretorio_transactions}")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M9 - Interação"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_interacao:
            dados_interacao[exercicio_id] = {}
        
        # M9: Contar apenas eventos JSON válidos, acumulando de forma segura
        try:
            contagem_eventos = 0
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        json.loads(linha)
                        contagem_eventos += 1
                    except json.JSONDecodeError:
                        continue # Ignora ruídos textuais ou linhas corrompidas
            
            # Evita sobrescrever dados caso haja múltiplos logs do mesmo aluno
            dados_interacao[exercicio_id][aluno_id] = dados_interacao[exercicio_id].get(aluno_id, 0) + contagem_eventos
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, alunos_dict in dados_interacao.items():
        valores_eventos = list(alunos_dict.values())
        
        # Filtro: Apenas alunos com eventos válidos mapeados
        valores_validos = [v for v in valores_eventos if v > 0]
        total_alunos_validos = len(valores_validos)
        
        # Significância Estatística
        if total_alunos_validos >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos, ddof=1)
            
            q1 = np.percentile(valores_validos, 25)
            q3 = np.percentile(valores_validos, 75)
            iqr = q3 - q1
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': total_alunos_validos,
                'Total_Eventos_Interacao_M9': sum(valores_validos),
                'Media_Interacoes_M9': round(media, 2),
                'Mediana_Interacoes_M9': round(mediana, 2),
                'Desvio_Padrao_M9': round(desvio_padrao, 2),
                'Q1_M9': round(q1, 2),
                'Q3_M9': round(q3, 2),
                'IQR_M9': round(iqr, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com interações válidas.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Mediana_Interacoes_M9', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M9 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_eventos_de_interacao(path_t)
