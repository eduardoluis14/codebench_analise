import os
import json
import pandas as pd
from pathlib import Path
from tqdm import tqdm

def calcular_discriminacao_m13(diretorio_transactions):
    base_path = Path(diretorio_transactions)
    
    print(f"Lendo logs em: {base_path.resolve()}")
    arquivos = list(base_path.glob("**/*.log"))
    
    if not arquivos:
        print("Nenhum arquivo .log encontrado.")
        return

    matriz_sucesso = {}
    tentativas_por_exercicio = {}

    print("Passo 1: Carregando logs e mapeando performance global...")
    for arquivo_log in tqdm(arquivos, desc="Processando Logs"):
        exercicio_id = arquivo_log.stem
        
        try:
            partes = arquivo_log.parts
            idx_trans = partes.index("transactions_exames_only")
            aluno_id = partes[idx_trans + 1]
        except (ValueError, IndexError):
            continue

        if aluno_id not in matriz_sucesso:
            matriz_sucesso[aluno_id] = {}
        
        if exercicio_id not in tentativas_por_exercicio:
            tentativas_por_exercicio[exercicio_id] = set()

        try:
            acertou = False
            fez_submissao = False
            with open(arquivo_log, 'r', encoding='utf-8') as f:
                for linha in f:
                    linha = linha.strip()
                    if not linha: continue
                    try:
                        evento = json.loads(linha)
                    except json.JSONDecodeError:
                        continue
                    
                    if evento.get('eventType') == 'submission':
                        fez_submissao = True
                        detalhes = evento.get('details', {})
                        try:
                            correctness = float(detalhes.get('correctness', 0))
                        except (ValueError, TypeError):
                            correctness = 0.0
                        
                        if correctness == 1.0:
                            acertou = True
            
            if fez_submissao:
                matriz_sucesso[aluno_id][exercicio_id] = acertou
                tentativas_por_exercicio[exercicio_id].add(aluno_id)
        except Exception:
            continue

    # Passo 2: Calcular Habilidade Global do Aluno (Taxa de Acerto Geral)
    aluno_performance = {}
    for aluno_id, questoes in matriz_sucesso.items():
        total_tentadas = len(questoes)
        if total_tentadas > 0:
            acertos = sum(1 for status in questoes.values() if status)
            aluno_performance[aluno_id] = acertos / total_tentadas

    if not aluno_performance:
        print("Nenhum dado válido de performance foi gerado.")
        return

    df_ranking = pd.DataFrame.from_dict(aluno_performance, orient='index', columns=['score'])
    
    # Divisão por Quartis
    q_high = df_ranking['score'].quantile(0.75)
    q_low = df_ranking['score'].quantile(0.25)
    
    alunos_top = set(df_ranking[df_ranking['score'] >= q_high].index)
    alunos_bottom = set(df_ranking[df_ranking['score'] <= q_low].index)

    # Passo 3: Calcular M13 por Exercício sem ler arquivos novamente
    relatorio = []
    for ex_id, alunos_que_tentaram in tentativas_por_exercicio.items():
        total_alunos = len(alunos_que_tentaram)
        
        # Significância estatística amostral
        if total_alunos >= 16:
            top_total = 0
            top_acertos = 0
            bot_total = 0
            bot_acertos = 0
            
            for aluno_id in alunos_que_tentaram:
                acertou = matriz_sucesso[aluno_id][ex_id]
                
                if aluno_id in alunos_top:
                    top_total += 1
                    if acertou: top_acertos += 1
                elif aluno_id in alunos_bottom:
                    bot_total += 1
                    if acertou: bot_acertos += 1
            
            if top_total > 0 and bot_total > 0:
                taxa_top = top_acertos / top_total
                taxa_bot = bot_acertos / bot_total
                m13 = taxa_top - taxa_bot
                
                relatorio.append({
                    'ID_Exercicio': ex_id,
                    'Qtd_Alunos_Validos': total_alunos,
                    'Alunos_Top_Avaliados': top_total,
                    'Alunos_Bot_Avaliados': bot_total,
                    'Media_Discriminacao_M13': round(m13, 3),
                    'Interpretacao': 'Excelente (>= 0.4)' if m13 >= 0.4 else ('Boa (0.3 - 0.39)' if m13 >= 0.3 else 'Fraca (< 0.3)')
                })

    if not relatorio:
        print("\nNenhum exercício gerou dados de discriminação válidos com o critério mínimo.")
        return

    df_final = pd.DataFrame(relatorio)
    df_final = df_final.sort_values(by='Media_Discriminacao_M13', ascending=False)
    
    caminho_do_script = Path(__file__).parent
    pasta_testes = caminho_do_script.parent
    output_file = pasta_testes / "exemplo" / "saida.csv"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(output_file, index=False)
    
    print(f"\nRelatório M13 salvo em: {output_file}")

caminho_base = Path(__file__).parent.parent.parent / "exemplo" / "transactions"
calcular_discriminacao_m13(caminho_base)
