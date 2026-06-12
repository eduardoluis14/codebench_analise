import shutil
from pathlib import Path

# Caminhos dos arquivos e pastas
arquivo_vip = Path('ids_questoes_de_prova_ipc.txt')
pasta_origem = Path('transactions')
pasta_destino = Path('transactions_provas')

print("Iniciando a filtragem dos logs de transacao...")

# Carrega a lista de IDs das questoes de prova
with open(arquivo_vip, 'r') as f:
    ids_vip = set(linha.strip() for linha in f if linha.strip())

# Busca todos os arquivos .log na pasta de origem
arquivos_log = list(pasta_origem.rglob("*.log"))
copiados = 0

for arquivo in arquivos_log:
    # O nome do arquivo sem a extensao e o ID do exercicio
    id_exercicio = arquivo.stem
    
    if id_exercicio in ids_vip:
        # Mantem a estrutura original das subpastas
        caminho_relativo = arquivo.relative_to(pasta_origem)
        caminho_novo = pasta_destino / caminho_relativo
        
        # Cria as pastas necessarias no destino
        caminho_novo.parent.mkdir(parents=True, exist_ok=True)
        
        # Faz a copia do arquivo
        shutil.copy2(arquivo, caminho_novo)
        copiados += 1

print(f"Filtragem concluida. Total de arquivos copiados: {copiados}")
