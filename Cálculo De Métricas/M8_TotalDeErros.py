import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

def calcular_total_de_erros(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # Dicionário estruturado: {id_exercicio: {id_aluno: {'erros': 0, 'submissoes': 0, 'sucesso': False}}}
    dados_erros = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print(f"Nenhum ficheiro .log encontrado em {diretorio_transactions}")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M8 - Total de Erros"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_erros:
            dados_erros[exercicio_id] = {}
        
        if aluno_id not in dados_erros[exercicio_id]:
            dados_erros[exercicio_id][aluno_id] = {'erros': 0, 'submissoes': 0, 'sucesso': False}

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
            
            # Ordenação cronológica real por datetime
            try:
                eventos.sort(key=lambda x: datetime.fromisoformat(x.get('dateTime', '').replace('Z', '+00:00')))
            except Exception:
                eventos.sort(key=lambda x: x.get('dateTime', ''))
            
            for evento in eventos:
                # Processamos apenas submissões e enquanto o aluno ainda não obteve sucesso
                if evento.get('eventType') == 'submission' and not dados_erros[exercicio_id][aluno_id]['sucesso']:
                    dados_erros[exercicio_id][aluno_id]['submissoes'] += 1
                    
                    detalhes = evento.get('details', {})
                    correctness_raw = detalhes.get('correctness')
                    
                    # Caso 1: Erro de execução/sintaxe (correctness ausente ou None) -> M7
                    if 'correctness' not in detalhes or correctness_raw is None:
                        dados_erros[exercicio_id][aluno_id]['erros'] += 1
                    else:
                        try:
                            correctness = float(correctness_raw)
                        except (ValueError, TypeError):
                            continue
                        
                        # Caso de Sucesso: interrompe o fluxo de erro para este aluno
                        if correctness == 1.0:
                            dados_erros[exercicio_id][aluno_id]['sucesso'] = True
                            break
                        # Caso 2: Erro de Lógica (correctness < 1.0) -> M6
                        elif correctness < 1.0:
                            dados_erros[exercicio_id][aluno_id]['erros'] += 1
                            
        except Exception:
            continue

    # Gerar relatório final
    relatorio = []
    for ex_id, alunos_dict in dados_erros.items():
        # Filtro: Extrai os erros acumulados apenas de quem fez submissões reais
        valores_validos = [v['erros'] for v in alunos_dict.values() if v['submissoes'] > 0]
        total_alunos_validos = len(valores_validos)
        
        # Critério mínimo de significância amostral
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
                'Total_Erros_Acumulados_M8': sum(valores_validos),
                'Media_Erros_M8': round(media, 2),
                'Mediana_Erros_M8': round(mediana, 2),
                'Desvio_Padrao_M8': round(desvio_padrao, 2),
                'Q1_M8': round(q1, 2),
                'Q3_M8': round(q3, 2),
                'IQR_M8': round(iqr, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com submissões.")
        return

    df = pd.DataFrame(relatorio)
    # Ordenar pela Mediana (exercícios com maior barreira de erros no topo)
    df = df.sort_values(by='Mediana_Erros_M8', ascending=False)

    output_file = "exemplo/saida.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M8 salvo em: {output_file}")

path_t = 'exemplo/transactions'
calcular_total_de_erros(path_t)
