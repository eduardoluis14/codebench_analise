import shutil
from pathlib import Path

# Caminhos dos arquivos e pastas
arquivo_vip = Path('ids_questoes_de_prova_ipc.txt')
pasta_origem = Path('exercises')
pasta_destino = Path('exercises_filtrada')

print("Iniciando a filtragem das solucoes de referencia...")

# Carrega a lista de IDs das questoes de prova
with open(arquivo_vip, 'r') as f:
    ids_vip = set(linha.strip() for linha in f if linha.strip())

# Lista apenas os diretorios presentes na origem
pastas_questoes = [p for p in pasta_origem.iterdir() if p.is_dir()]
copiadas = 0

for pasta in pastas_questoes:
    id_exercicio = pasta.name
    
    if id_exercicio in ids_vip:
        destino_pasta = pasta_destino / id_exercicio
        
        # Copia a pasta inteira contendo o codigo da solucao
        shutil.copytree(pasta, destino_pasta, dirs_exist_ok=True)
        copiadas += 1

print(f"Filtragem concluida. Total de pastas copiadas: {copiadas}")
