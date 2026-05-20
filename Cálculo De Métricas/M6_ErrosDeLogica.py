import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from datetime import datetime

def calcular_erros_de_logica(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    # Dicionário: {id_exercicio: {id_aluno: {'erros': 0, 'submissoes_validas': 0, 'sucesso': False}}}
    dados_logica = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum ficheiro .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M6 - Erros de Lógica"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_logica:
            dados_logica[exercicio_id] = {}
        
        if aluno_id not in dados_logica[exercicio_id]:
            dados_logica[exercicio_id][aluno_id] = {'erros': 0, 'submissoes_validas': 0, 'sucesso': False}

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
            
            # Ordenação cronológica para garantir que paramos no primeiro sucesso
            try:
                eventos.sort(key=lambda x: datetime.fromisoformat(x.get('dateTime', '').replace('Z', '+00:00')))
            except Exception:
                eventos.sort(key=lambda x: x.get('dateTime', ''))
            
            for evento in eventos:
                if evento.get('eventType') == 'submission':
                    detalhes = evento.get('details', {})
                    
                    if 'correctness' in detalhes and detalhes.get('correctness') is not None:
                        dados_logica[exercicio_id][aluno_id]['submissoes_validas'] += 1
                        
                        try:
                            correctness = float(detalhes['correctness'])
                        except (ValueError, TypeError):
                            continue 
                        
                        if correctness == 1.0:
                            dados_logica[exercicio_id][aluno_id]['sucesso'] = True
                            break 
                        elif correctness < 1.0:
                            dados_logica[exercicio_id][aluno_id]['erros'] += 1
                            
        except Exception:
            continue

    relatorio = []
    for ex_id, alunos_dict in dados_logica.items():
        valores_validos = [v['erros'] for v in alunos_dict.values() if v['submissoes_validas'] > 0]
        total_alunos_validos = len(valores_validos)
        
        if total_alunos_validos >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos, ddof=1) if total_alunos_validos > 1 else 0
            
            q1 = np.percentile(valores_validos, 25)
            q3 = np.percentile(valores_validos, 75)
            iqr = q3 - q1
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': total_alunos_validos,
                'Total_Erros_Logica': sum(valores_validos),
                'Media_Erros_Logica_M6': round(media, 2),
                'Mediana_Erros_Logica_M6': round(mediana, 2),
                'Desvio_Padrao_M6': round(desvio_padrao, 2),
                'Q1_M6': round(q1, 2),
                'Q3_M6': round(q3, 2),
                'IQR_M6': round(iqr, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com submissões válidas.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Mediana_Erros_Logica_M6', ascending=False)
    
    caminho_do_script = Path(__file__).parent
    pasta_testes = caminho_do_script.parent
    output_file = pasta_testes / "exemplo" / "saida.csv"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)

caminho_base = Path(__file__).parent.parent.parent / "exemplo" / "transactions"
calcular_erros_de_logica(caminho_base)
