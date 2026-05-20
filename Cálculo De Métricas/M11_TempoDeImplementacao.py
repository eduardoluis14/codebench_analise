import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

def calcular_tempo_implementacao(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # dicionário: {id_exercicio: {id_aluno: tempo_total_segundos}}
    dados_tempo = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum ficheiro .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M11 - Tempo de Implementação"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        eventos = []
        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        obj = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    
                    dt_str = obj.get('dateTime', '').replace('Z', '+00:00')
                    if not dt_str: continue
                    
                    try:
                        dt = datetime.fromisoformat(dt_str)
                    except ValueError:
                        dt = pd.to_datetime(dt_str).to_pydatetime()
                        
                    eventos.append({'dt': dt, 'type': obj.get('eventType'), 'details': obj.get('details', {})})
            
            if not eventos: continue
            
            # Garantir ordem cronológica
            eventos.sort(key=lambda x: x['dt'])
            
            primeira_interacao = eventos[0]['dt']
            tempo_acumulado = 0
            ultimo_evento_dt = primeira_interacao
            sucesso = False

            for i in range(1, len(eventos)):
                evento_atual = eventos[i]
                
                # Calcular diferença de tempo em segundos
                diff = (evento_atual['dt'] - ultimo_evento_dt).total_seconds()
                
                # Regra M11: Timeout de 5 minutos (300 segundos)
                if diff <= 300:
                    tempo_acumulado += diff
                
                ultimo_evento_dt = evento_atual['dt']

                # Parar o cronómetro na primeira submissão correta
                if evento_atual['type'] == 'submission' and float(evento_atual['details'].get('correctness', 0)) == 1.0:
                    sucesso = True
                    break
            
            # O exercício só entra se o aluno conseguiu chegar à solução correta
            if sucesso:
                if exercicio_id not in dados_tempo:
                    dados_tempo[exercicio_id] = {}
                dados_tempo[exercicio_id][aluno_id] = tempo_acumulado
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, alunos_dict in dados_tempo.items():
        tempos = list(alunos_dict.values())
        
        # Descartar tempos absurdamente curtos (copy-paste imediato)
        tempos_validos = [t for t in tempos if t > 2.0]
        total_alunos_validos = len(tempos_validos)
        
        # Significância Estatística
        if total_alunos_validos >= 16:
            # Cálculos convertidos diretamente para Minutos
            tempos_minutos = [t / 60.0 for t in tempos_validos]
            
            media_min = np.mean(tempos_minutos)
            mediana_min = np.median(tempos_minutos)
            desvio_padrao_min = np.std(tempos_minutos, ddof=1)
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Sucesso': total_alunos_validos,
                'Media_Tempo_Minutos_M11': round(media_min, 2),
                'Mediana_Tempo_Minutos_M11': round(mediana_min, 2),
                'Desvio_Padrao_Tempo_M11': round(desvio_padrao_min, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com sucesso.")
        return

    df = pd.DataFrame(relatorio)
    # Ordenar pela Mediana do tempo
    df = df.sort_values(by='Mediana_Tempo_Minutos_M11', ascending=False)
    
    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M11 salvo. Top 10 exercícios mais demorados:")

path_t = 'exemplo/transactions'
calcular_tempo_implementacao(path_t)
