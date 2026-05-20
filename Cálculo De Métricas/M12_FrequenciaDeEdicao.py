import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm

def calcular_frequencia_edicao(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    dados_edicao = {}

    print(f"A ler logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum ficheiro .log encontrado.")
        return

    for arquivo_log in tqdm(arquivos, desc="A analisar M12 - Frequência de Edição"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            aluno_id = "desconhecido"

        if exercicio_id not in dados_edicao:
            dados_edicao[exercicio_id] = {}
        
        if aluno_id not in dados_edicao[exercicio_id]:
            dados_edicao[exercicio_id][aluno_id] = 0

        try:
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue 
                    
                    if evento.get('eventType') == 'generic':
                        dados_edicao[exercicio_id][aluno_id] += 1
                            
        except Exception:
            continue

    relatorio = []
    for ex_id, alunos_dict in dados_edicao.items():
        valores = list(alunos_dict.values())
        
        valores_validos = [v for v in valores if v > 0]
        total_alunos_validos = len(valores_validos)
        
        if total_alunos_validos >= 16:
            media = np.mean(valores_validos)
            mediana = np.median(valores_validos)
            desvio_padrao = np.std(valores_validos)
            
            relatorio.append({
                'ID_Exercicio': ex_id,
                'Qtd_Alunos_Validos': total_alunos_validos,
                'Total_Eventos_Edicao': sum(valores_validos),
                'Media_Edicoes_M12': round(media, 2),
                'Mediana_Edicoes_M12': round(mediana, 2),
                'Desvio_Padrao_M12': round(desvio_padrao, 2)
            })

    if not relatorio:
        print("\nNenhum exercício atingiu o critério mínimo de 16 alunos com edições válidas.")
        return

    df = pd.DataFrame(relatorio)
    df = df.sort_values(by='Mediana_Edicoes_M12', ascending=False)
    
    caminho_do_script = Path(__file__).parent
    pasta_testes = caminho_do_script.parent
    output_file = pasta_testes / "exemplo" / "saida.csv"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    
    print(f"\nRelatório M12 salvo em: {output_file}")

caminho_base = Path(__file__).parent.parent.parent / "exemplo" / "saida"
calcular_frequencia_edicao(caminho_base)
