import ast
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from collections import Counter

class ASTMetricsExtractor(ast.NodeVisitor):
    def __init__(self):
        self.metrics = {
            'max_depth': 0,
            'num_loops': 0,
            'num_ifs': 0,
            'variaveis_unicas': set(),
            'complexidade_ciclomatica': 1, 
            'num_funcoes': 0,
            'tem_recursao': 0 
        }
        self.current_depth = 0

    def _enter_control_flow(self, node):
        self.current_depth += 1
        self.metrics['max_depth'] = max(self.metrics['max_depth'], self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_FunctionDef(self, node):
        self.metrics['num_funcoes'] += 1
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call) and getattr(sub_node.func, 'id', None) == node.name:
                self.metrics['tem_recursao'] = 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.metrics['num_ifs'] += 1
        self.metrics['complexidade_ciclomatica'] += 1 
        self._enter_control_flow(node)

    def visit_For(self, node):
        self.metrics['num_loops'] += 1
        self.metrics['complexidade_ciclomatica'] += 1 
        self._enter_control_flow(node)

    def visit_While(self, node):
        self.metrics['num_loops'] += 1
        self.metrics['complexidade_ciclomatica'] += 1 
        self._enter_control_flow(node)

    def visit_ListComp(self, node):
        self.metrics['num_loops'] += 1
        self.metrics['complexidade_ciclomatica'] += 1
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.metrics['num_loops'] += 1
        self.metrics['complexidade_ciclomatica'] += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.metrics['complexidade_ciclomatica'] += len(node.values) - 1
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.metrics['variaveis_unicas'].add(node.id)
        self.generic_visit(node)


class ASTPlanDetector(ast.NodeVisitor):
    def __init__(self, global_metrics):
        self.global_metrics = global_metrics
        self.pattern_counts = Counter()
        
        self.in_if = 0
        self.in_for = 0
        self.in_while = 0

    def visit_If(self, node):
        # 5. Condicional aninhado (Se já estamos dentro de um if e achamos outro)
        if self.in_if > 0:
            self.pattern_counts["Condicional aninhado"] += 1

        # Controle para não contar 'elif' como um if solto:
        if getattr(node, 'is_elif', False):
            pass # Já foi classificado pelo pai, apenas segue a árvore
        else:
            # 2. Condicional simples (Sem else)
            if len(node.orelse) == 0:
                self.pattern_counts["Condicional simples"] += 1
            
            # 4. Condicional encadeado (if/elif/...)
            elif len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                self.pattern_counts["Condicional encadeado"] += 1
                
                # Marca todos os 'elifs' da corrente para não dobrar a contagem
                curr = node
                while len(curr.orelse) == 1 and isinstance(curr.orelse[0], ast.If):
                    curr = curr.orelse[0]
                    curr.is_elif = True
                    
            # 3. Condicional composto (if/else normal)
            else:
                self.pattern_counts["Condicional composto"] += 1

        self.in_if += 1
        self.generic_visit(node)
        self.in_if -= 1

    def visit_For(self, node):
        self.in_for += 1
        
        # 10. Iteração por índice (usa range)
        if isinstance(node.iter, ast.Call) and getattr(node.iter.func, 'id', None) == 'range':
            self.pattern_counts["Estrutura linear (lista/string) - iteração por índice"] += 1
        # 11. Iteração por valor (direto na lista, string ou tupla)
        elif isinstance(node.iter, (ast.Name, ast.List, ast.Tuple, ast.Str)):
            self.pattern_counts["Estrutura linear (lista/string) - iteração por valor"] += 1

        self.generic_visit(node)
        self.in_for -= 1

    def visit_While(self, node):
        self.in_while += 1
        self.generic_visit(node)
        self.in_while -= 1

    # Detecta contadores e acumuladores: +=, -=
    def visit_AugAssign(self, node):
        if isinstance(node.op, (ast.Add, ast.Sub)):
            # Se for += 1 é incremento, senão é acúmulo
            is_increment = isinstance(node.value, ast.Constant) and node.value.value == 1
            
            if self.in_for > 0:
                if is_increment:
                    self.pattern_counts["Repetição - incremento de variável"] += 1
                else:
                    self.pattern_counts["Repetição - acúmulo de variável"] += 1
                    
            if self.in_while > 0:
                if is_increment:
                    self.pattern_counts["Repetição com condição - incremento de variável"] += 1
                else:
                    self.pattern_counts["Repetição com condição - acúmulo de variável"] += 1
                    
        self.generic_visit(node)

    # Detecta contadores e acumuladores padrão: x = x + 1
    def visit_Assign(self, node):
        if isinstance(node.value, ast.BinOp) and isinstance(node.value.op, (ast.Add, ast.Sub)):
            targets = [getattr(t, 'id', None) for t in node.targets if isinstance(t, ast.Name)]
            left = getattr(node.value.left, 'id', None) if isinstance(node.value.left, ast.Name) else None
            right = getattr(node.value.right, 'id', None) if isinstance(node.value.right, ast.Name) else None

            # Verifica se está atualizando a mesma variável (ex: x = x + algo)
            for t in targets:
                if t is not None and (t == left or t == right):
                    is_increment = False
                    if isinstance(node.value.right, ast.Constant) and node.value.right.value == 1:
                        is_increment = True
                    elif isinstance(node.value.left, ast.Constant) and node.value.left.value == 1:
                        is_increment = True
                    
                    if self.in_for > 0:
                        if is_increment:
                            self.pattern_counts["Repetição - incremento de variável"] += 1
                        else:
                            self.pattern_counts["Repetição - acúmulo de variável"] += 1
                            
                    if self.in_while > 0:
                        if is_increment:
                            self.pattern_counts["Repetição com condição - incremento de variável"] += 1
                        else:
                            self.pattern_counts["Repetição com condição - acúmulo de variável"] += 1

        self.generic_visit(node)


def analisar_arquivo(caminho_arquivo):
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            codigo = f.read()
            linhas_validas = [l for l in codigo.splitlines() if l.strip() and not l.strip().startswith('#')]
            loc = len(linhas_validas) if len(linhas_validas) > 0 else 1 
            
            tree = ast.parse(codigo)
        
        extractor = ASTMetricsExtractor()
        extractor.visit(tree)
        metrics = extractor.metrics
        
        detector = ASTPlanDetector(metrics)
        detector.visit(tree)
        
        features = {
            'LOC': loc,
            'AST_Profundidade_Fluxo': metrics['max_depth'],
            'AST_Complexidade_Ciclomatica': metrics['complexidade_ciclomatica'],
            'AST_Qtd_Loops': metrics['num_loops'],
            'AST_Qtd_Ifs': metrics['num_ifs'],
            'AST_Qtd_Variaveis': len(metrics['variaveis_unicas']),
            'AST_Qtd_Funcoes': metrics['num_funcoes'],
            'AST_Tem_Recursao': metrics['tem_recursao'],
        }
        
        features['Norm_Complexidade_Por_LOC'] = round(features['AST_Complexidade_Ciclomatica'] / loc, 4)
        features['Norm_Ifs_Por_LOC'] = round(features['AST_Qtd_Ifs'] / loc, 4)
        features['Norm_Loops_Por_LOC'] = round(features['AST_Qtd_Loops'] / loc, 4)

        # 1. Input/output sequencial
        if features['AST_Qtd_Loops'] == 0 and features['AST_Qtd_Ifs'] == 0:
            detector.pattern_counts["Input/output sequencial"] += 1

        # LÓGICA DE HIERARQUIA GLOBAL (Mantém apenas o MAIS complexo)
        # Ordem do mais difícil (Listas) para o mais fácil (Sequencial)
        ordem_complexidade = [
            "Estrutura linear (lista/string) - iteração por índice",
            "Estrutura linear (lista/string) - iteração por valor",
            "Repetição com condição - acúmulo de variável",
            "Repetição com condição - incremento de variável",
            "Repetição - acúmulo de variável",
            "Repetição - incremento de variável",
            "Condicional aninhado",
            "Condicional encadeado",
            "Condicional composto",
            "Condicional simples",
            "Input/output sequencial"
        ]

        # Encontra qual foi o padrão mais complexo ativado neste código
        padrao_dominante = None
        for p in ordem_complexidade:
            if detector.pattern_counts.get(p, 0) > 0:
                padrao_dominante = p
                break  # Achou o "chefão", para a busca!

        # Zera todos os outros padrões, deixando APENAS o dominante
        if padrao_dominante:
            for p in ordem_complexidade:
                if p != padrao_dominante:
                    detector.pattern_counts[p] = 0

        padroes_mapeados = [
            "Input/output sequencial",
            "Condicional simples",
            "Condicional composto",
            "Condicional encadeado",
            "Condicional aninhado",
            "Repetição - incremento de variável",
            "Repetição - acúmulo de variável",
            "Repetição com condição - incremento de variável",
            "Repetição com condição - acúmulo de variável",
            "Estrutura linear (lista/string) - iteração por índice",
            "Estrutura linear (lista/string) - iteração por valor"
        ]
        
        for p in padroes_mapeados:
            features[f'Freq_{p.replace(" ", "_").replace("/", "_")}'] = detector.pattern_counts.get(p, 0)
            
        encontrados = [p for p, count in detector.pattern_counts.items() if count > 0]
        features['padroes_str'] = "; ".join(encontrados) if encontrados else "Sem Padrão Mapeado"
        
        return features
    except Exception:
        return None

def processar_exercicios_v11(path_exercises):
    base_path = Path(path_exercises)
    resultados = []

    pastas_exercicios = [p for p in base_path.iterdir() if p.is_dir()]
    print(f"Encontradas {len(pastas_exercicios)} pastas em {base_path}")

    for pasta in tqdm(pastas_exercicios, desc="Extraindo Taxonomia Estrutural (V11)"):
        arquivos_py = list(pasta.glob("*.py"))
        arquivo_alvo = None
        
        if not arquivos_py: continue
            
        for py in arquivos_py:
            if "sample_solution" in py.name:
                arquivo_alvo = py
                break
                
        if not arquivo_alvo:
            arquivo_alvo = max(arquivos_py, key=lambda p: p.stat().st_size)
            
        features = analisar_arquivo(arquivo_alvo)
        
        if features:
            features['id_exercicio'] = pasta.name
            resultados.append(features)

    df = pd.DataFrame(resultados)
    cols = ['id_exercicio', 'padroes_str'] + [c for c in df.columns if c not in ['id_exercicio', 'padroes_str']]
    return df[cols]

# EXECUÇÃO DO PIPELINE
caminho_do_script = Path(__file__).parent         
pasta_testes = caminho_do_script.parent            
pasta_tcc = pasta_testes.parent                   

caminho_exercises = pasta_tcc / "DataSet" / "exercises"

df_features_final = processar_exercicios_v11(caminho_exercises)

if not df_features_final.empty:
    output_file = caminho_do_script / "features_ast_publicacao_padroes_completos_v11.csv"
    df_features_final.to_csv(output_file, index=False)
    print(f"\nSucesso! Arquivo V11 salvo em: {output_file}")
