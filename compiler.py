import re
from typing import List, Dict, Any

KEYWORDS = {
    'int','char','float','double','void','return','if','else','while',
    'for','do','break','continue','switch','case','default','printf',
    'scanf','include','main','struct','typedef','const','unsigned'
}
OPERATORS_MULTI = {'==','!=','<=','>=','&&','||','++','--','+=','-=','<<','>>'}
SINGLE_OPS = set('=+-*/%&|!><^~')
VALID_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-*/%=<>!&|^~(){}[];,.:# \t\n\r\'\"\\?")

def _classify(tok: str) -> str:
    if tok in KEYWORDS:                               return 'keyword'
    if tok in OPERATORS_MULTI:                        return 'operator'
    if re.match(r'^[a-zA-Z_]\w*$', tok):             return 'identifier'
    if re.match(r'^\d+(\.\d+)?$', tok):              return 'number'
    if tok.startswith('"') or tok.startswith("'"):    return 'literal'
    if len(tok) == 1 and tok in SINGLE_OPS:          return 'operator'
    return 'punctuation'

# ── Phase 1: Lexical Analysis ─────────────────────────────────────────────────
def lexical_analysis(code: str) -> Dict[str, Any]:
    errors = []
    lines = code.split('\n')
    for lineno, line in enumerate(lines, 1):
        # Ignore preprocessor for valid char check in this simple simulation
        if line.strip().startswith('#'): continue
        
        for i, char in enumerate(line):
            if char not in VALID_CHARS:
                return {
                    'error': f"Lexical Error: Invalid symbol '{char}' at line {lineno}",
                    'tokens': [], 'summary': {}, 'total': 0
                }
    
    pattern = r'"[^"]*"|\'[^\']{0,8}\'|[a-zA-Z_]\w*|\d+\.\d+|\d+|==|!=|<=|>=|&&|\|\||[^\s]'
    raw = re.findall(pattern, code)
    tokens, counts = [], {'keyword':0,'identifier':0,'operator':0,'punctuation':0,'literal':0,'number':0}
    for tok in raw:
        kind = _classify(tok)
        tokens.append({'text': tok, 'type': kind})
        counts[kind] = counts.get(kind, 0) + 1
    return {'error': None, 'tokens': tokens, 'summary': counts, 'total': len(tokens)}

# ── Phase 2: Syntax Analysis ──────────────────────────────────────────────────
def _build_parse_tree(code: str) -> List[Dict]:
    tree = [{'depth': 0, 'label': 'TranslationUnit'}]
    # Preprocessor
    for m in re.finditer(r'#\s*include\s*[<"]([^>"]+)[>"]', code):
        tree.append({'depth': 1, 'label': f'PreprocessorDir → #include <{m.group(1)}>'})
    # Function declarations
    for m in re.finditer(r'(int|void|char|float|double)\s+(\w+)\s*\(([^)]*)\)\s*\{', code):
        ret, fname, params = m.group(1), m.group(2), m.group(3).strip() or 'void'
        tree.append({'depth': 1, 'label': f'FunctionDecl → {ret} {fname}({params})'})
        tree.append({'depth': 2, 'label': 'CompoundStmt { … }'})
        body_start = m.end()
        # Local decls
        for dm in re.finditer(r'(int|char|float|double)\s+(\w+)\s*(?:=\s*([^;]+))?;', code[body_start:]):
            val = f' = {dm.group(3).strip()}' if dm.group(3) else ''
            tree.append({'depth': 3, 'label': f'DeclStmt → {dm.group(1)} {dm.group(2)}{val}'})
    return tree

def syntax_analysis(code: str) -> Dict[str, Any]:
    op, cp = code.count('('), code.count(')')
    ob, cb = code.count('{'), code.count('}')
    sq_o, sq_c = code.count('['), code.count(']')
    semi = code.count(';')
    
    if op != cp:
        return {'error': f"Syntax Error: Unbalanced parentheses — {op} open, {cp} close", 'valid': False}
    if ob != cb:
        return {'error': f"Syntax Error: Unbalanced braces — {ob} open, {cb} close", 'valid': False}
    if sq_o != sq_c:
        return {'error': f"Syntax Error: Unbalanced brackets — {sq_o} open, {sq_c} close", 'valid': False}
    
    # Basic missing semicolon check
    lines = code.split('\n')
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('//') or s.endswith('{') or s.endswith('}') or s.endswith(';') or s.endswith(':'):
            continue
        if any(kw in s for kw in ['if', 'while', 'for', 'else']):
            continue
        if any(typ in s for typ in ['int', 'float', 'char', 'double', 'return', 'printf', 'scanf']) or '=' in s:
            return {'error': f"Syntax Error: Missing semicolon at line {i}", 'valid': False}

    return {
        'error': None,
        'valid': True,
        'checks': {
            'parentheses': {'open': op, 'close': cp, 'balanced': True},
            'braces':       {'open': ob, 'close': cb, 'balanced': True},
            'semicolons':   semi,
            'char_literals': len(re.findall(r"'[^']{0,8}'", code)),
        },
        'parse_tree': _build_parse_tree(code),
    }

# ── Phase 3: Semantic Analysis ────────────────────────────────────────────────
def semantic_analysis(code: str) -> Dict[str, Any]:
    sym = []
    declared_vars = {} # name -> type
    current_func = 'global'
    errors = []

    def repl(m): return '\n' * m.group(0).count('\n')
    no_comments_code = re.sub(r'/\*.*?\*/', repl, code, flags=re.DOTALL)
    no_comments_code = re.sub(r'//[^\n]*', '', no_comments_code)

    # Simple identification of declared variables
    for i, line in enumerate(no_comments_code.split('\n'), 1):
        # Function
        m = re.match(r'\s*(int|void|char|float|double)\s+([a-zA-Z_]\w*)\s*\(', line)
        if m:
            fname = m.group(2)
            sym.append({'name':fname,'kind':'function','type':m.group(1),'value':'–','scope':'global','line':i})
            declared_vars[fname] = m.group(1)
            continue
        
        # Variable
        m = re.match(r"\s*(int|char|float|double)\s+([a-zA-Z_]\w*)\s*(?:=\s*([^;]+))?;", line)
        if m:
            vtype, vname = m.group(1), m.group(2)
            if vname in declared_vars:
                errors.append(f"Semantic Error: Variable '{vname}' redeclared at line {i}")
            declared_vars[vname] = vtype
            val = m.group(3).strip() if m.group(3) else 'uninit'
            sym.append({'name':vname,'kind':'variable','type':vtype,'value':val,'scope':'main','line':i})
            
            # Type check literal assignment
            if vtype == 'int' and m.group(3) and '.' in m.group(3):
                errors.append(f"Semantic Error: Type mismatch at line {i} — cannot assign float to int '{vname}'")
            continue
            
    # Check for undeclared variables in usage
    no_literals_code = re.sub(r'"[^"]*"', '""', no_comments_code)
    no_literals_code = re.sub(r"'[^']*'", "''", no_literals_code)

    for i, line in enumerate(no_literals_code.split('\n'), 1):
        if 'int ' in line or 'char ' in line or 'float ' in line or 'double ' in line: continue
        if line.strip().startswith('#'): continue
        
        # Find identifiers being used (not keywords)
        used = re.findall(r'\b([a-zA-Z_]\w*)\b', line)
        for u in used:
            if u in KEYWORDS or u.isdigit(): continue
            if u not in declared_vars and u not in ['printf', 'scanf', 'main']:
                 errors.append(f"Semantic Error: Variable '{u}' used but not declared at line {i}")
                 break

    if errors:
        return {'error': errors[0], 'symbol_table': sym, 'type_checks': [], 'errors': errors}

    return {'error': None, 'symbol_table': sym, 'type_checks': [], 'errors': []}

# ── Phase 4: Intermediate Code (3-Address Code) ───────────────────────────────
def intermediate_code(code: str) -> Dict[str, Any]:
    instrs = []
    n, t = [1], [0]

    def add(stmt, comment=''):
        instrs.append({'n': n[0], 'code': stmt, 'comment': comment})
        n[0] += 1

    def tmp():
        t[0] += 1
        return f't{t[0]}'

    def lbl():
        t[0] += 1
        return f'L{t[0]}'

    clean = re.sub(r'//[^\n]*', '', code)
    clean = re.sub(r'/\*.*?\*/', '', clean, flags=re.DOTALL)

    # Variable initializations
    for m in re.finditer(r"(int|char|float|double)\s+(\w+)\s*=\s*('[^']*'|\d+(?:\.\d+)?|\"[^\"]*\");", clean):
        add(f"{m.group(2)} = {m.group(3)}", f'{m.group(1)} init')

    # Assignments
    for m in re.finditer(r'\b([a-zA-Z_]\w*)\s*=\s*([^=;][^;]*);', clean):
        lhs, rhs = m.group(1).strip(), m.group(2).strip()
        if lhs in KEYWORDS: continue
        if any(f"{lhs} =" in ins['code'] and 'init' in ins.get('comment','') for ins in instrs):
            continue
        ops = re.split(r'([+\-*/])', rhs)
        if len(ops) > 1:
            t1 = tmp()
            add(f'{t1} = {rhs}', 'computation')
            add(f'{lhs} = {t1}', 'store')
        else:
            add(f'{lhs} = {rhs}', 'assign')

    # If/else
    seen_conds = set()
    for m in re.finditer(r'\bif\s*\((.+?)\)(?=\s*[\{;])', clean, re.DOTALL):
        cond = m.group(1).strip()
        if cond in seen_conds: continue
        seen_conds.add(cond)
        tv = tmp()
        add(f'{tv} = {cond[:50]}', 'condition')
        l_true, l_false, l_end = lbl(), lbl(), lbl()
        add(f'if {tv} goto {l_true}', 'branch')
        add(f'goto {l_false}', 'else branch')
        add(f'{l_true}:', '── then ──')
        add(f'[then body]', '')
        add(f'goto {l_end}', 'skip else')
        add(f'{l_false}:', '── else ──')
        add(f'[else body]', '')
        add(f'{l_end}:', '── end if ──')

    # While loops
    for m in re.finditer(r'\bwhile\s*\((.+?)\)\s*\{', clean):
        cond = m.group(1).strip()
        ls, le = lbl(), lbl()
        tc = tmp()
        add(f'{ls}:', '── while ──')
        add(f'{tc} = {cond[:50]}', 'loop cond')
        add(f'if not {tc} goto {le}', 'exit loop')
        add(f'[loop body]', '')
        add(f'goto {ls}', 'back edge')
        add(f'{le}:', '── end while ──')

    # For loops
    for m in re.finditer(r'\bfor\s*\(([^;]*);([^;]*);([^)]*)\)', clean):
        init, cond, step = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        ls, le = lbl(), lbl()
        tc = tmp()
        add(f'{init}', 'for init')
        add(f'{ls}:', '── for ──')
        add(f'{tc} = {cond}', 'for cond')
        add(f'if not {tc} goto {le}', 'exit for')
        add(f'[loop body]', '')
        add(f'{step}', 'step')
        add(f'goto {ls}', 'back edge')
        add(f'{le}:', '── end for ──')

    for m in re.finditer(r'\b(printf|scanf)\s*\(([^)]+)\)', clean):
        add(f'{m.group(1)}({m.group(2).strip()[:40]})', 'I/O call')

    for m in re.finditer(r'\breturn\s+([^;]+);', clean):
        add(f'return {m.group(1).strip()}', 'return')

    if not instrs:
        add('[No analyzable statements found]', '')

    return {'error': None, 'instructions': instrs}

# ── Phase 5: Code Optimization ────────────────────────────────────────────────
def optimization(code: str) -> Dict[str, Any]:
    opts = []
    const_vars = {}
    for m in re.finditer(r"(int|char|float|double)\s+(\w+)\s*=\s*('[^']*'|\d+(?:\.\d+)?)\s*;", code):
        const_vars[m.group(2)] = m.group(3)
    
    opts.append({'icon':'📌','name':'Constant Folding','description':f'Compile-time constants: {", ".join(list(const_vars.keys())[:3])}' if const_vars else 'No constant folding candidates','applied':bool(const_vars)})
    
    can_fold = bool(const_vars) and ('if' in code or 'while' in code)
    opts.append({'icon':'🌿','name':'Dead Branch Elimination','description':'Dead branches removed' if can_fold else 'No foldable branches','applied':can_fold})
    
    has_sc = '&&' in code or '||' in code
    opts.append({'icon':'⚡','name':'Short-Circuit Evaluation','description':'Logical ops optimized' if has_sc else 'No short-circuit candidates','applied':has_sc})
    
    exprs = re.findall(r'[a-zA-Z_]\w*\s*(?:==|!=|<=|>=|>|<)\s*\S+', code)
    repeated = len(exprs) - len(set(exprs))
    opts.append({'icon':'♻️','name':'Common Sub-Expression Elim.','description':f'{repeated} repeated expressions collapsed' if repeated else 'No repeated sub-expressions','applied':repeated > 0})
    
    has_mult = '*' in code or '/' in code
    opts.append({'icon':'💡','name':'Strength Reduction','description':'Multiply/divide replaced with bit-shifts' if has_mult else 'No strength reduction candidates','applied':has_mult})

    var_names = list(dict.fromkeys(re.findall(r'(?:int|char|float|double)\s+(\w+)', code)))
    opts.append({'icon':'📦','name':'Register Allocation','description':f'{len(var_names)} variable(s) cached in registers' if var_names else 'No variables to allocate','applied':bool(var_names)})

    has_loop = 'for' in code or 'while' in code
    opts.append({'icon':'🔁','name':'Loop Unrolling','description':'Loop unrolling applied' if has_loop else 'No loops found','applied':has_loop})

    result = "Constants folded; dead branches removed" if const_vars else "Expressions simplified"
    return {'error': None, 'optimizations': opts, 'optimized_result': result}

# ── Phase 6: Target Code Generation ──────────────────────────────────────────
def target_code(code: str) -> Dict[str, Any]:
    instrs = []
    def add(addr='', instr='', arg='', comment=''):
        instrs.append({'addr': addr, 'instr': instr, 'arg': arg, 'comment': comment})

    var_decls = re.findall(r'(int|char|float|double)\s+(\w+)', code)
    has_loop = bool(re.search(r'\b(for|while)\b', code))
    has_printf = 'printf' in code
    func_m = re.search(r'(int|void)\s+(\w+)\s*\(', code)
    fname = func_m.group(2) if func_m else 'main'
    stack_size = max(16, len(var_decls) * 8)

    add('0x0000', 'SECTION', '.text', '; code segment')
    add('0x0000', 'GLOBAL', fname, f'; export {fname}')
    add()
    add('0x0000', f'{fname}:', '', '; entry')
    add('0x0000', 'PUSH', 'rbp', '; save rbp')
    add('0x0001', 'MOV', 'rbp, rsp', '; set frame')
    add('0x0004', 'SUB', f'rsp, {stack_size}', f'; {stack_size}B stack')
    add()

    offset = 4
    for vtype, vname in var_decls:
        m = re.search(rf"{re.escape(vtype)}\s+{re.escape(vname)}\s*=\s*('[^']*'|\d+)", code)
        if m:
            val = m.group(1)
            add(hex(offset), 'MOV', f'DWORD[rbp-{offset}], {val}', f'; {vname} = {val}')
            offset += 8
    add()
    if has_printf:
        add(hex(offset), 'LEA', 'rcx, [fmt_out]', '; printf format')
        add(hex(offset+4), 'CALL', 'printf', '; call printf')
    add()
    add(hex(offset+8), 'XOR', 'eax, eax', '; return 0')
    add(hex(offset+10), 'LEAVE', '', '; restore stack')
    add(hex(offset+11), 'RET', '', '; return')
    
    return {'error': None, 'instructions': instrs}

def compile_all(code: str) -> Dict[str, Any]:
    phases = {}
    
    res = lexical_analysis(code)
    phases['lexical'] = res
    if res.get('error'): return phases
    
    res = syntax_analysis(code)
    phases['syntax'] = res
    if res.get('error'): return phases
    
    res = semantic_analysis(code)
    phases['semantic'] = res
    if res.get('error'): return phases
    
    phases['intermediate'] = intermediate_code(code)
    phases['optimization'] = optimization(code)
    phases['target'] = target_code(code)
    
    return phases
