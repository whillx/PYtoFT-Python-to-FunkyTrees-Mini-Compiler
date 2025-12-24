# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import copy
import os
import sys
import time
from pathlib import Path
from graphlib import TopologicalSorter

# Python to Funkey Trees Converter by Whills v1.0

class Substituter(ast.NodeTransformer):
    def __init__(self, env, func_returns, constants=None, substitute_args=True):
        self.env = env
        self.func_returns = func_returns
        self.constants = constants or {}
        self.substitute_args = substitute_args # substitute_args is used to avoid argument substitution in function calls within main loop process

    def visit_Name(self, node):
        if node.id in exclude_vars:
            return node  # Don't substitute excluded variables
        if node.id in self.env:
            return copy.deepcopy(self.env[node.id])
        elif node.id in self.constants:
            return copy.deepcopy(self.constants[node.id])
        return node

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            name = node.func.id
            if name in self.func_returns:
                expr = copy.deepcopy(self.func_returns[name])
                # Get the function definition to map parameters
                func_def = functions_dic[name]  # Assuming 'functions_dic' is in scope or passed
                if len(node.args) != len(func_def.args.args):
                    raise ValueError(f"Argument count mismatch for {name}")
                # Create a temp env for parameter substitution
                if self.substitute_args:
                    param_env = {}
                    for i, arg in enumerate(func_def.args.args):
                        substituted_arg = copy.deepcopy(node.args[i])
                        substituted_arg = Substituter(self.env, self.func_returns, self.constants, self.substitute_args).visit(substituted_arg)
                        ast.fix_missing_locations(substituted_arg)
                        param_env[arg.arg] = substituted_arg
                else:
                    param_env = {arg.arg: copy.deepcopy(node.args[i]) for i, arg in enumerate(func_def.args.args)}
                # Substitute parameters in the expression
                expr = Substituter(param_env, self.func_returns, self.constants, self.substitute_args).visit(expr)
                ast.fix_missing_locations(expr)
                return expr
        return self.generic_visit(node)


def replace_none(node, replacement):
    if isinstance(node, ast.Name) and node.id == 'None':
        return copy.deepcopy(replacement)
    elif isinstance(node, ast.IfExp):
        node.body = replace_none(node.body, replacement)
        node.orelse = replace_none(node.orelse, replacement)
        return node
    else:
        # For other nodes, recurse if they have child nodes
        for child in ast.iter_child_nodes(node):
            replace_none(child, replacement)
        return node

def replace_none_with_orelse(node):
    if isinstance(node, ast.IfExp):
        if not (isinstance(node.orelse, ast.Name) and node.orelse.id == 'None'):
            if isinstance(node.body, ast.IfExp) and isinstance(node.body.orelse, ast.Name) and node.body.orelse.id == 'None':
                node.body.orelse = copy.deepcopy(node.orelse)
            replace_none_with_orelse(node.body)
            replace_none_with_orelse(node.orelse)

def reduce_block_to_return(body_stmts, env, func_returns):
    local_env = env.copy()
    ret_expr = None
    for stmt in body_stmts:
        if isinstance(stmt, ast.Return):
            ret_value = copy.deepcopy(stmt.value)
            ret_value = Substituter(local_env, func_returns).visit(ret_value)
            ast.fix_missing_locations(ret_value)
            if ret_expr is None:
                ret_expr = ret_value
            else:
                replace_none(ret_expr, ret_value)
        elif isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if isinstance(target, ast.Name):
                value = copy.deepcopy(stmt.value)
                value = Substituter(local_env, func_returns).visit(value)
                ast.fix_missing_locations(value)
                local_env[target.id] = value
        elif isinstance(stmt, ast.AugAssign):
            if isinstance(stmt.target, ast.Name):
                var_name = stmt.target.id
                current_value = local_env.get(var_name, ast.Name(id=var_name))
                value = copy.deepcopy(stmt.value)
                value = Substituter(local_env, func_returns).visit(value)
                ast.fix_missing_locations(value)
                new_value = ast.BinOp(left=current_value, op=stmt.op, right=value)
                ast.fix_missing_locations(new_value)
                local_env[var_name] = new_value
        elif isinstance(stmt, ast.If):
            ret_expr = reduce_if_chain(stmt, local_env, func_returns)
        elif isinstance(stmt, ast.Pass):
            pass
        elif isinstance(stmt, ast.Expr):
            pass  # Skip expressions
        else:
            raise ValueError(f"Unsupported statement in block: {type(stmt)}")
    return ret_expr

def reduce_if_chain(node, env, func_returns):
    if isinstance(node, ast.If):
        test = copy.deepcopy(node.test)
        test = Substituter(env, func_returns).visit(test)
        ast.fix_missing_locations(test)
        body_ret = reduce_block_to_return(node.body, env, func_returns)
        if len(node.orelse) == 0:
            orelse_ret = ast.Name(id='None')
        else:
            orelse_ret = reduce_block_to_return(node.orelse, env, func_returns)
        return ast.IfExp(test=test, body=body_ret, orelse=orelse_ret)
    else:
        raise ValueError("Not an if")

def contains_return(block):
    for stmt in block:
        if isinstance(stmt, ast.Return):
            return True
        if isinstance(stmt, ast.If):
            if contains_return(stmt.body) or contains_return(stmt.orelse):
                return True
    return False

def reduce_function_to_expr(func_def, func_returns):
    env = {}
    ret_expr = None

    for stmt in func_def.body:
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                raise ValueError("Only simple assignments supported")

            value = copy.deepcopy(stmt.value)
            value = Substituter(env, func_returns).visit(value)
            ast.fix_missing_locations(value)
            env[target.id] = value

        elif isinstance(stmt, ast.AugAssign):
            if not isinstance(stmt.target, ast.Name):
                raise ValueError("Only simple augmented assignments supported")

            var_name = stmt.target.id
            if var_name not in env:
                raise ValueError(f"Variable {var_name} not defined before augmented assignment")

            current_value = copy.deepcopy(env[var_name])
            aug_value = copy.deepcopy(stmt.value)
            aug_value = Substituter(env, func_returns).visit(aug_value)
            ast.fix_missing_locations(aug_value)
            new_value = ast.BinOp(left=current_value, op=stmt.op, right=aug_value)
            ast.fix_missing_locations(new_value)
            env[var_name] = new_value

        elif isinstance(stmt, ast.If):
            if contains_return([stmt]):
                if_expr = reduce_if_chain(stmt, env, func_returns)
                if ret_expr is None:
                    ret_expr = if_expr
                else:
                    replace_none(ret_expr, if_expr)
            else:
                # Handle as assignment if, supporting elif
                body_dict = reduce_block_to_dict(stmt.body, env, func_returns)
                orelse_dict = reduce_block_to_dict(stmt.orelse, env, func_returns)
                test = copy.deepcopy(stmt.test)
                test = Substituter(env, func_returns).visit(test)
                ast.fix_missing_locations(test)
                all_targets = set(body_dict) | set(orelse_dict)
                for target in all_targets:
                    body_expr = body_dict.get(target, ast.Name(id=target))
                    orelse_expr = orelse_dict.get(target, ast.Name(id=target))
                    ternary = ast.IfExp(test=test, body=body_expr, orelse=orelse_expr)
                    env[target] = ternary

        elif isinstance(stmt, ast.Return):
            ret_value = copy.deepcopy(stmt.value)
            ret_value = Substituter(env, func_returns).visit(ret_value)
            ast.fix_missing_locations(ret_value)
            if ret_expr is None:
                ret_expr = ret_value
            else:
                replace_none(ret_expr, ret_value)

        elif isinstance(stmt, ast.Global):
            pass  # Ignore global declarations

        else:
            raise ValueError("Unsupported statement in helper")

    if ret_expr is None:
        raise ValueError(f"{func_def.name} has no return")
    replace_none_with_orelse(ret_expr)
    return ret_expr

def reduce_block_to_dict(block_stmts, env, func_returns, constants=None):
    result = {}
    for stmt in block_stmts:
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                raise ValueError("Only simple assignments supported")
            value = copy.deepcopy(stmt.value)
            value = Substituter(env, func_returns, constants, False).visit(value)
            ast.fix_missing_locations(value)
            result[target.id] = value
        elif isinstance(stmt, ast.AugAssign):
            if not isinstance(stmt.target, ast.Name):
                raise ValueError("Only simple augmented assignments supported")
            var_name = stmt.target.id
            current_value = env.get(var_name, ast.Name(id=var_name))
            value = copy.deepcopy(stmt.value)
            value = Substituter(env, func_returns, constants, False).visit(value)
            ast.fix_missing_locations(value)
            new_value = ast.BinOp(left=current_value, op=stmt.op, right=value)
            ast.fix_missing_locations(new_value)
            result[var_name] = new_value
        elif isinstance(stmt, ast.If):
            body_dict = reduce_block_to_dict(stmt.body, env, func_returns, constants)
            orelse_dict = reduce_block_to_dict(stmt.orelse, env, func_returns, constants)
            test = copy.deepcopy(stmt.test)
            test = Substituter(env, func_returns).visit(test)
            ast.fix_missing_locations(test)
            all_targets = set(body_dict) | set(orelse_dict)
            for target in all_targets:
                body_expr = body_dict.get(target, ast.Name(id=target))
                orelse_expr = orelse_dict.get(target, ast.Name(id=target))
                ternary = ast.IfExp(test=test, body=body_expr, orelse=orelse_expr)
                result[target] = ternary

        elif isinstance(stmt, ast.Return):
            pass  # Skip returns in assignment blocks
        elif isinstance(stmt, ast.Expr):
            pass  # Skip expressions
        elif isinstance(stmt, ast.Pass):
            pass
        else:
            raise ValueError("Unsupported statement in block")
    return result

def emit_c_style(node):
    if isinstance(node, ast.BinOp):
        left = emit_c_style(node.left)
        right = emit_c_style(node.right)
        op = type(node.op).__name__
        ops = {
            "Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "Mod": "%",
            "Pow": "**"  # adjust if needed
        }
        return f"({left} {ops[op]} {right})"

    elif isinstance(node, ast.Name):
        return node.id

    elif isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return str(node.value).lower()
        else:
            return repr(node.value)

    elif isinstance(node, ast.Call):
        func = emit_c_style(node.func)
        args = ", ".join(emit_c_style(a) for a in node.args)
        return f"{func}({args})"

    elif isinstance(node, ast.IfExp):
        test = emit_c_style(node.test)
        body = emit_c_style(node.body)
        orelse = emit_c_style(node.orelse)
        return f"({test} ? {body} : {orelse})"

    elif isinstance(node, ast.UnaryOp):
        operand = emit_c_style(node.operand)
        if isinstance(node.op, ast.USub):   # unary minus
            return f"-{operand}"
        elif isinstance(node.op, ast.Not):  # Python 'not'
            return f"!{operand}"            # convert to FT '!'
        else:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        
    elif isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise ValueError("Only single comparisons supported")
        left = emit_c_style(node.left)
        right = emit_c_style(node.comparators[0])
        op = node.ops[0]
        ops = {
            ast.Eq: "==",
            ast.NotEq: "!=",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">="
        }
        op_str = ops[type(op)]
        return f"({left} {op_str} {right})"
    elif isinstance(node, ast.BoolOp):
        op = node.op
        if isinstance(op, ast.And):
            op_str = "&"
        elif isinstance(op, ast.Or):
            op_str = "|"
        else:
            raise ValueError(f"Unsupported boolean operator: {type(op)}")
        parts = [emit_c_style(v) for v in node.values]
        return "(" + f" {op_str} ".join(parts) + ")"

    elif isinstance(node, ast.Attribute):
        # Simply emit "process.pitchControl" as "pitchControl"
        return node.attr
    
    elif isinstance(node, ast.List):
        pass # FT does not support lists directly

    else:
        raise ValueError(f"Unsupported node: {type(node)}")

def load_py_file() -> list:

    def get_executable_dir() -> Path:
        if getattr(sys, 'frozen', False):
            # Running as a PyInstaller executable
            return Path(os.path.dirname(sys.executable))
        else:
            # Running as a normal Python script
            return Path(os.path.dirname(os.path.abspath(__file__))).parent

    p = get_executable_dir()
    #print(p)
    py_files = [f for f in sorted(p.iterdir()) if f.is_file() and f.suffix == ".py" and not f.name.startswith("_")]
    return py_files


functions_dic = {}
function_returns_dic = {}
# excule_vars is a set of variable names to be excluded from substitution, first, we don't want to substitute global variables, 
# second, we want to exclude the local variable in the main loop function and user-specified variables in exclude list
exclude_vars = {}

def py_to_ft(_source_file_path, print_output: bool = False) -> dict:
    global exclude_vars

    print("Converting variables ....\n")
    start_time = time.time()
    
    # ---------- load source ----------
    source_py_path = _source_file_path
    with source_py_path.open("r", encoding="utf-8") as source_file:
        tree = ast.parse(source_file.read())

    # ---------- Collect names from FT_functions.py to skip ---------- 
    ft_names = set()
    ft_file = Path(__file__).resolve().parent / "FT_functions.py"
    if ft_file.exists():
        with ft_file.open("r", encoding="utf-8") as f:
            ft_tree = ast.parse(f.read())
        for node in ft_tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        ft_names.add(target.id)

    # ---------- collect globals and extract main loop name and exclude list----------

    global_exprs = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            target = node.targets[0]
            if isinstance(target, ast.Name):
                global_exprs[target.id] = node.value

    # Extract main_loop_name from globals
    try:
        main_loop_name = ast.literal_eval(global_exprs['main_loop_name'])
    except KeyError:
        main_loop_name = '_process'

    # Extract exclude list if present
    exclude_list = []
    if 'exclude' in global_exprs:
        try:
            exclude_list = ast.literal_eval(global_exprs['exclude'])
            if not isinstance(exclude_list, list):
                exclude_list = []
        except:
            exclude_list = []


    exclude_vars = set(global_exprs.keys())
    exclude_vars.update(exclude_list)

    # ---------- collect functions ----------

    def collect_functions(node, functions):
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    functions[item.name] = item
        for child in ast.iter_child_nodes(node):
            collect_functions(child, functions)

    def collect_called_functions(func_def):
        called = set()
        for node in ast.walk(func_def):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)
        return called

    collect_functions(tree, functions_dic)

    # Collect and process imported modules (excluding _FT_functions)
    processed_modules = set()

    def process_module(mod_name):
        if mod_name in processed_modules or '_FT_functions' in mod_name:
            return
        p = Path(__file__).resolve().parent.parent
        processed_modules.add(mod_name)
        parts = mod_name.split('.')
        if len(parts) == 1:
            mod_file = p / f"{mod_name}.py"
        else:
            mod_file = p.joinpath(*parts[:-1]) / f"{parts[-1]}.py"
        if mod_file.exists():
            with mod_file.open("r", encoding="utf-8") as f:
                mod_tree = ast.parse(f.read())
            collect_functions(mod_tree, functions_dic)
            # Collect its own imports
            mod_imported = set()
            for node in ast.walk(mod_tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        m = alias.name
                        if '_FT_functions' not in m:
                            mod_imported.add(m)
                elif isinstance(node, ast.ImportFrom):
                    m = node.module
                    if m and '_FT_functions' not in m:
                        mod_imported.add(m)
            for m in mod_imported:
                process_module(m)

    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod_name = alias.name
                if '_FT_functions' not in mod_name:
                    imported_modules.add(mod_name)
        elif isinstance(node, ast.ImportFrom):
            mod_name = node.module
            if mod_name and '_FT_functions' not in mod_name:
                imported_modules.add(mod_name)

    for mod_name in imported_modules:
        process_module(mod_name)

    # Build dependency graph for helper functions
    helper_funcs = {name: func for name, func in functions_dic.items() if name != main_loop_name}
    dependencies = {name: collect_called_functions(func) & set(helper_funcs.keys()) for name, func in helper_funcs.items()}

    # Topological sort
    ts = TopologicalSorter(dependencies)
    ts_order = list(ts.static_order())

    # Reduce functions in dependency order
    for name in ts_order:
        func = helper_funcs[name]
        try:
            function_returns_dic[name] = reduce_function_to_expr(func, function_returns_dic)
        except ValueError:
            print(f"WARNING: Function {name} cannot be reduced\n")  # Ignore functions that cannot be reduced (e.g., no return, unsupported statements)
            pass

    # ---------- find main process ----------

    process_func = functions_dic.get(main_loop_name)
    # process_found = process_func is not None

    local_vars = set()
    if process_func:
        for node in ast.walk(process_func):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        local_vars.add(target.id)
        main_body = [node for node in tree.body if (isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign) or isinstance(node, ast.If))] + process_func.body
    else:
        main_body = [node for node in tree.body if (isinstance(node, ast.Assign) or isinstance(node, ast.AugAssign) or isinstance(node, ast.If))]
        print(f"main loop function not found, will convert only global variables")

    exclude_vars.update(local_vars)

    # ---------- ordered reduction ----------

    env = {}
    constants = {}

    for stmt in main_body:
        if isinstance(stmt, ast.Assign):
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                raise ValueError("Only simple assignments supported")

            if isinstance(stmt.value, ast.Constant):
                constants[target.id] = stmt.value
            else:
                value = copy.deepcopy(stmt.value)
                value = Substituter(env, function_returns_dic).visit(value) # substitute_args=False does not work here, it prevents function calls arguments in main process from being substituted
                ast.fix_missing_locations(value)

                env[target.id] = value

        elif isinstance(stmt, ast.AugAssign):
            if not isinstance(stmt.target, ast.Name):
                raise ValueError("Only simple augmented assignments supported")

            var_name = stmt.target.id
            current_value = env.get(var_name, ast.Name(id=var_name))
            value = copy.deepcopy(stmt.value)
            value = Substituter(env, function_returns_dic, constants, False).visit(value)
            ast.fix_missing_locations(value)
            new_value = ast.BinOp(left=current_value, op=stmt.op, right=value)
            ast.fix_missing_locations(new_value)
            env[var_name] = new_value

        elif isinstance(stmt, ast.If):
            body_dict = reduce_block_to_dict(stmt.body, env, function_returns_dic, constants)
            orelse_dict = reduce_block_to_dict(stmt.orelse, env, function_returns_dic, constants)
            test = copy.deepcopy(stmt.test)
            test = Substituter(env, function_returns_dic, substitute_args=False).visit(test)
            ast.fix_missing_locations(test)
            all_targets = set(body_dict) | set(orelse_dict)
            for target in all_targets:
                body_expr = body_dict.get(target, ast.Name(id=target))
                orelse_expr = orelse_dict.get(target, ast.Name(id=target))
                ternary = ast.IfExp(test=test, body=body_expr, orelse=orelse_expr)
                env[target] = ternary

        else:
            continue

    # Add constants that were not overridden
    env = {**constants, **env}

    # ---------- emit results ----------

    # for name, expr in global_exprs.items():
    #     if name not in env and name not in exclude_list and name not in ft_names:
    #         # if not (isinstance(expr, ast.Constant) and isinstance(expr.value, str)):
    #         print(f"{name} = {emit_c_style(expr)}\n")
    export_dic = {}
    for name, expr in env.items():
        if name not in exclude_list and name not in ft_names and name != "main_loop_name" and name != "exclude":
            export_dic[name] = emit_c_style(expr)
            if print_output:
                print(f"{name} = {emit_c_style(expr)}\n")
    # print(exclude_vars)
    end_time = time.time()
    print(f"Conversion completed in {end_time - start_time:.4f} seconds.\n")
    return export_dic
    

if __name__ == "__main__":
    py_to_ft(load_py_file()[0], print_output=True)