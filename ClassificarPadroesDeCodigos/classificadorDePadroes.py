import ast
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from collections import Counter

# Parte 1: EXTRATOR DE MÉTRICAS 
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


# Parte 2: DETECTOR DE PLANOS
class ASTPlanDetector(ast.NodeVisitor):
    def __init__(self, global_metrics):
        self.global_metrics = global_metrics
        self.pattern_counts = Counter()
        
        self.in_loop = 0
        self.in_if = 0
        
        self.tem_input = False
        self.tem_output = False
        self.tem_branching_real = False
        self.decomp_mod_10 = 0
        self.decomp_div_10 = 0
        self.initialized_vars = set() 

    def _enter_control_flow(self, node):
        self.generic_visit(node)

    def visit_Return(self, node):
        if node.value is not None:
            self.tem_output = True
        self.generic_visit(node)

    def visit_If(self, node):
        if node.orelse:
            self.tem_branching_real = True
        
        for stmt in node.body:
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break)):
                self.pattern_counts["Guarded Exception Plan"] += 1
                break 
                
        if self.in_loop > 0:
            for stmt in node.body:
                if isinstance(stmt, ast.Raise):
                    self.pattern_counts["Validate Plan"] += 1
                    break
                elif isinstance(stmt, ast.Return):
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value in [False, None, 0, "", -1, "ERRO"]:
                        self.pattern_counts["Validate Plan"] += 1
                        break
                    elif isinstance(stmt.value, (ast.List, ast.Dict, ast.Tuple)):
                        if hasattr(stmt.value, 'elts') and len(stmt.value.elts) == 0:
                            self.pattern_counts["Validate Plan"] += 1
                            break
                        elif hasattr(stmt.value, 'keys') and len(stmt.value.keys) == 0:
                            self.pattern_counts["Validate Plan"] += 1
                            break
                
        self.in_if += 1
        self._enter_control_flow(node)
        self.in_if -= 1

    def visit_For(self, node):
        self.in_loop += 1
        self._enter_control_flow(node)
        self.in_loop -= 1

    def visit_While(self, node):
        self.in_loop += 1
        self._enter_control_flow(node)
        self.in_loop -= 1

    def visit_ListComp(self, node):
        for gen in node.generators:
            if gen.ifs:
                self.pattern_counts["Filter A Collection Plan"] += 1
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        for gen in node.generators:
            if gen.ifs:
                self.pattern_counts["Filter A Collection Plan"] += 1
        self.generic_visit(node)

    def visit_Compare(self, node):
        if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Mod):
            if isinstance(node.left.right, ast.Constant) and node.left.right.value in [2, 3, 5, 10]:
                self.pattern_counts["Divisibility Plan"] += 1
        self.generic_visit(node)

    def visit_BinOp(self, node):
        if self.in_loop > 0:
            if isinstance(node.op, ast.Mod) and isinstance(node.right, ast.Constant) and node.right.value == 10:
                self.decomp_mod_10 += 1
            if isinstance(node.op, ast.FloorDiv) and isinstance(node.right, ast.Constant) and getattr(node.right, 'value', None) == 10:
                self.decomp_div_10 += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        if getattr(node.func, 'id', None) == 'input':
            self.tem_input = True
        if getattr(node.func, 'id', None) == 'print':
            self.tem_output = True

        if getattr(node.func, 'id', None) in ['min', 'max']:
            self.pattern_counts["Min/Max Plan"] += 1
            
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'join':
            if isinstance(node.func.value, ast.Constant) and isinstance(node.func.value.value, str):
                if len(node.func.value.value) > 0: 
                    self.pattern_counts["Delimiting Strings Plan"] += 1
            
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
            if self.in_loop > 0 and self.in_if > 0:
                self.pattern_counts["Filter A Collection Plan"] += 1
                
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'ArgumentParser':
            self.pattern_counts["Command Line Arguments Plan"] += 1
        elif getattr(node.func, 'id', None) == 'ArgumentParser':
            self.pattern_counts["Command Line Arguments Plan"] += 1
                
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            targets = [elt.id for elt in node.targets[0].elts if isinstance(elt, ast.Name)]
            values = [elt.id for elt in node.value.elts if isinstance(elt, ast.Name)]
            if len(targets) == 2 and targets[0] != targets[1] and set(targets) == set(values):
                self.pattern_counts["Triangular Swap Plan"] += 1

        if isinstance(node.value, ast.Constant):
            if isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                if self.in_loop == 0 and self.global_metrics['num_loops'] > 0:
                    if isinstance(node.value.value, (int, bool, str)) and node.value.value in [0, 1, "", False, True]:
                        if var_name not in self.initialized_vars:
                            self.pattern_counts["Initialisation Plan"] += 1
                            self.initialized_vars.add(var_name)
                
                elif self.in_loop > 0 and self.in_if > 0:
                    if isinstance(node.value.value, bool):
                        self.pattern_counts["Indicators Plan"] += 1
                    
        elif isinstance(node.value, (ast.List, ast.Dict)): 
            if isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                if self.in_loop == 0 and self.global_metrics['num_loops'] > 0:
                    if var_name not in self.initialized_vars:
                        self.pattern_counts["Initialisation Plan"] += 1
                        self.initialized_vars.add(var_name)

        self.generic_visit(node)
        
    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Subscript):
            if isinstance(node.op, (ast.Add, ast.Sub)):
                if self.in_loop > 0:
                    self.pattern_counts["MultiCount Plan"] += 1
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id == 'sys' and node.attr == 'argv':
            self.pattern_counts["Command Line Arguments Plan"] += 1
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

        if detector.decomp_mod_10 > 0 and detector.decomp_div_10 > 0:
            detector.pattern_counts["Number Decomposition Plan"] += 1

        if features['AST_Qtd_Loops'] == 0 and features['AST_Qtd_Ifs'] == 0:
            if detector.tem_input and detector.tem_output:
                detector.pattern_counts["Input-Process-Output Plan"] += 1

        if features['AST_Qtd_Loops'] == 0 and features['AST_Qtd_Ifs'] > 0:
            if detector.tem_branching_real:
                detector.pattern_counts["Conditional Branching Plan"] += 1
                
        padroes_mapeados = [
            "Guarded Exception Plan", "Divisibility Plan", "Min/Max Plan", 
            "Triangular Swap Plan", "Initialisation Plan", "Number Decomposition Plan", 
            "Command Line Arguments Plan", "Filter A Collection Plan", "Validate Plan",            
            "Indicators Plan", "Delimiting Strings Plan", "MultiCount Plan",
            "Input-Process-Output Plan", "Conditional Branching Plan"         
        ]
        
        for p in padroes_mapeados:
            features[f'Freq_{p.replace(" ", "_").replace("/", "_")}'] = detector.pattern_counts.get(p, 0)
            
        encontrados = [p for p, count in detector.pattern_counts.items() if count > 0]
        features['padroes_str'] = "; ".join(encontrados) if encontrados else "Sem Padrão Mapeado"
        
        return features
    except Exception:
        return None

def processar_exercicios_v9(path_exercises):
    base_path = Path(path_exercises)
    resultados = []

    pastas_exercicios = [p for p in base_path.iterdir() if p.is_dir()]
    print(f"Encontradas {len(pastas_exercicios)} pastas em {base_path}")

    for pasta in tqdm(pastas_exercicios, desc="Extraindo Features Estruturais (V9 Finalíssima)"):
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

df_features_final = processar_exercicios_v9(caminho_exercises)

if not df_features_final.empty:
    output_file = caminho_do_script / "features_ast_publicacao_padroes_completos_v9.csv"
    df_features_final.to_csv(output_file, index=False)
    print(f"\nSucesso! Arquivo V9 Final salvo em: {output_file}")
