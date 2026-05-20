import ast
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from collections import Counter

class ASTPatternAnalyzer(ast.NodeVisitor):
    def __init__(self):
        # Contador de frequência para os Padrões
        self.pattern_counts = Counter()
        
        # Métricas Estruturais e de Engenharia de Software
        self.structural_metrics = {
            'max_depth': 0,
            'num_loops': 0,
            'num_ifs': 0,
            'variaveis_unicas': set(),
            'complexidade_ciclomatica': 1, # Base de McCabe (caminho linear)
            'num_funcoes': 0,
            'tem_recursao': 0 # Binário: 1 (sim), 0 (não)
        }
        self.current_control_depth = 0
        
        # Flags de contexto para padrões complexos
        self.in_loop = 0
        self.in_if = 0

    # --- CONTROLE DE FLUXO E CONTEXTO ---
    def _enter_control_flow(self, node):
        self.current_control_depth += 1
        self.structural_metrics['max_depth'] = max(self.structural_metrics['max_depth'], self.current_control_depth)
        self.generic_visit(node)
        self.current_control_depth -= 1

    def visit_FunctionDef(self, node):
        self.structural_metrics['num_funcoes'] += 1
        
        for sub_node in ast.walk(node):
            if isinstance(sub_node, ast.Call) and getattr(sub_node.func, 'id', None) == node.name:
                self.structural_metrics['tem_recursao'] = 1
                    
        self.generic_visit(node)

    def visit_If(self, node):
        self.structural_metrics['num_ifs'] += 1
        self.structural_metrics['complexidade_ciclomatica'] += 1 
        
        for stmt in node.body:
            # 1. Guarded Exception Plan (Raadt Original - interrupções genéricas)
            if isinstance(stmt, (ast.Return, ast.Raise, ast.Break)):
                self.pattern_counts["Guarded Exception Plan"] += 1
                
            # Validate Plan (Interrupção de rejeição explícita em loop)
            if self.in_loop > 0:
                if isinstance(stmt, ast.Raise):
                    self.pattern_counts["Validate Plan"] += 1
                elif isinstance(stmt, ast.Return):
                    if isinstance(stmt.value, ast.Constant) and stmt.value.value in [False, None]:
                        self.pattern_counts["Validate Plan"] += 1
                
        self.in_if += 1
        self._enter_control_flow(node)
        self.in_if -= 1

    def visit_For(self, node):
        self.structural_metrics['num_loops'] += 1
        self.structural_metrics['complexidade_ciclomatica'] += 1 
        self.in_loop += 1
        self._enter_control_flow(node)
        self.in_loop -= 1

    def visit_While(self, node):
        self.structural_metrics['num_loops'] += 1
        self.structural_metrics['complexidade_ciclomatica'] += 1 
        self.in_loop += 1
        self._enter_control_flow(node)
        self.in_loop -= 1

    def visit_ListComp(self, node):
        self.structural_metrics['num_loops'] += 1
        self.structural_metrics['complexidade_ciclomatica'] += 1
        
        # Filter A Collection Plan (List Comprehension com If)
        for gen in node.generators:
            if gen.ifs:
                self.pattern_counts["Filter A Collection Plan"] += 1
                
        self.generic_visit(node)
        
    def visit_DictComp(self, node):
        self.structural_metrics['num_loops'] += 1
        self.structural_metrics['complexidade_ciclomatica'] += 1
        for gen in node.generators:
            if gen.ifs:
                self.pattern_counts["Filter A Collection Plan"] += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.structural_metrics['complexidade_ciclomatica'] += len(node.values) - 1
        self.generic_visit(node)
        
    def visit_ExceptHandler(self, node):
        self.structural_metrics['complexidade_ciclomatica'] += 1
        self._enter_control_flow(node)
        
    def visit_With(self, node):
        self.structural_metrics['complexidade_ciclomatica'] += 1
        self._enter_control_flow(node)

    def visit_Assert(self, node):
        self.structural_metrics['complexidade_ciclomatica'] += 1
        self.generic_visit(node)

    #  Identificação de padrões de expressão
    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Mod):
            if isinstance(node.right, ast.Constant) and isinstance(node.right.value, int):
                if node.right.value in [2, 3, 5, 10]:
                    self.pattern_counts["Divisibility Plan"] += 1
                if node.right.value == 10:
                    self.pattern_counts["Number Decomposition Plan"] += 1

        if isinstance(node.op, ast.FloorDiv):
            if isinstance(node.right, ast.Constant) and getattr(node.right, 'value', None) == 10:
                self.pattern_counts["Number Decomposition Plan"] += 1

        self.generic_visit(node)

    def visit_Call(self, node):
        # Min/Max Plan
        if getattr(node.func, 'id', None) in ['min', 'max']:
            self.pattern_counts["Min/Max Plan"] += 1
            
        # Delimiting Strings Plan (Uso idiomático de .join com delimitador REAL)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'join':
            if isinstance(node.func.value, ast.Constant) and isinstance(node.func.value.value, str):
                if len(node.func.value.value) > 0: # Ignora "".join()
                    self.pattern_counts["Delimiting Strings Plan"] += 1
            
        # Filter A Collection Plan (Versão .append dentro de if e loop)
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'append':
            if self.in_loop > 0 and self.in_if > 0:
                self.pattern_counts["Filter A Collection Plan"] += 1
                
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.structural_metrics['variaveis_unicas'].add(node.id)
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Triangular Swap Plan
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            self.pattern_counts["Triangular Swap Plan"] += 1

        # Initialisation e Flags
        if isinstance(node.value, ast.Constant):
            # Initialisation Plan (Acontece fora de loops geramente)
            if self.in_loop == 0:
                if isinstance(node.value.value, bool) or node.value.value in [0, 1, ""]:
                    self.pattern_counts["Initialisation Plan"] += 1
            
            # Indicators Plan (Flag booleana reatribuída dentro de if num loop)
            elif self.in_loop > 0 and self.in_if > 0:
                if isinstance(node.value.value, bool):
                    self.pattern_counts["Indicators Plan"] += 1
                    
        elif isinstance(node.value, (ast.List, ast.Dict)): 
            if self.in_loop == 0:
                self.pattern_counts["Initialisation Plan"] += 1

        self.generic_visit(node)
        
    def visit_AugAssign(self, node):
        # MultiCount Plan (Exige estar dentro de um iterador)
        if isinstance(node.target, ast.Subscript):
            if isinstance(node.op, (ast.Add, ast.Sub)):
                if self.in_loop > 0:
                    self.pattern_counts["MultiCount Plan"] += 1
                
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Command Line Arguments Plan
        if isinstance(node.value, ast.Name) and node.value.id == 'sys' and node.attr == 'argv':
            self.pattern_counts["Command Line Arguments Plan"] += 1
        self.generic_visit(node)

    def visit_Import(self, node):
        # Command Line Arguments Plan
        for alias in node.names:
            if alias.name == 'argparse':
                self.pattern_counts["Command Line Arguments Plan"] += 1
        self.generic_visit(node)


def analisar_arquivo(caminho_arquivo):
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            codigo = f.read()
            linhas_validas = [l for l in codigo.splitlines() if l.strip() and not l.strip().startswith('#')]
            loc = len(linhas_validas) if len(linhas_validas) > 0 else 1 
            
            tree = ast.parse(codigo)
        
        analyzer = ASTPatternAnalyzer()
        analyzer.visit(tree)
        
        features = {
            'LOC': loc,
            'AST_Profundidade_Fluxo': analyzer.structural_metrics['max_depth'],
            'AST_Complexidade_Ciclomatica': analyzer.structural_metrics['complexidade_ciclomatica'],
            'AST_Qtd_Loops': analyzer.structural_metrics['num_loops'],
            'AST_Qtd_Ifs': analyzer.structural_metrics['num_ifs'],
            'AST_Qtd_Variaveis': len(analyzer.structural_metrics['variaveis_unicas']),
            'AST_Qtd_Funcoes': analyzer.structural_metrics['num_funcoes'],
            'AST_Tem_Recursao': analyzer.structural_metrics['tem_recursao'],
        }
        
        features['Norm_Complexidade_Por_LOC'] = round(features['AST_Complexidade_Ciclomatica'] / loc, 4)
        features['Norm_Ifs_Por_LOC'] = round(features['AST_Qtd_Ifs'] / loc, 4)
        features['Norm_Loops_Por_LOC'] = round(features['AST_Qtd_Loops'] / loc, 4)

        # OS 12 PADRÕES OFICIAIS
        padroes_mapeados = [
            "Guarded Exception Plan", 
            "Divisibility Plan", 
            "Min/Max Plan", 
            "Triangular Swap Plan", 
            "Initialisation Plan",
            "Number Decomposition Plan", 
            "Command Line Arguments Plan",
            "Filter A Collection Plan", 
            "Validate Plan",            
            "Indicators Plan",          
            "Delimiting Strings Plan",  
            "MultiCount Plan"           
        ]
        
        for p in padroes_mapeados:
            features[f'Freq_{p.replace(" ", "_").replace("/", "_")}'] = analyzer.pattern_counts.get(p, 0)
            
        encontrados = [p for p, count in analyzer.pattern_counts.items() if count > 0]
        features['padroes_str'] = "; ".join(encontrados) if encontrados else "Sem Padrão Mapeado"
        
        return features
    except Exception:
        return None

def processar_exercicios_v5(path_exercises):
    base_path = Path(path_exercises)
    resultados = []

    pastas_exercicios = [p for p in base_path.iterdir() if p.is_dir()]
    print(f"Encontradas {len(pastas_exercicios)} pastas em {base_path}")

    for pasta in tqdm(pastas_exercicios, desc="Extraindo Features Estruturais (AST)"):
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

df_features_final = processar_exercicios_v5(caminho_exercises)

if not df_features_final.empty:
    output_file = caminho_do_script / "features_ast_padroes_completos.csv"
    
    df_features_final.to_csv(output_file, index=False)
    
    print(f"\nSucesso! Gerado arquivo com {len(df_features_final)} exercícios classificados.")
    print(f"Salvo em: {output_file}")
else:
    print("\nO DataFrame está vazio. Verifique os caminhos da pasta exercises.")
