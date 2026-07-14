# Minimal LAMAGUE demo: transpile a simple LAMAGUE program to Python and execute it.

import ast
import sys

# Very tiny parser for the subset used in the demo (assignment, print, for-loop, if)

def parse_lamague(source: str):
    """Parse a tiny subset of LAMAGUE into a Python AST.
    Supports:
      var <name> = num<int>
      @print txt<"..."> [optional additional expr]
      @for var <i> in range<num<a>, num<b>> { ... }
      @if <cond> { ... } else { ... }
    This is only for demonstration, not a full implementation.
    """
    lines = [ln.strip() for ln in source.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    stmts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('var '):
            # assignment
            _, rest = line.split('var ', 1)
            name, expr = rest.split('=', 1)
            name = name.strip()
            expr = expr.strip()
            if expr.startswith('num<') and expr.endswith('>'):
                value = int(expr[5:-1])
                stmts.append(ast.Assign(targets=[ast.Name(id=name, ctx=ast.Store())],
                                         value=ast.Constant(value=value)))
            else:
                raise ValueError('Unsupported literal')
            i += 1
        elif line.startswith('@print'):
            # @print txt<"Hello"> optional extra expr
            parts = line.split(' ', 1)[1] if ' ' in line else ''
            if parts.startswith('txt<') and parts.endswith('>'):
                txt = parts[4:-1]
                # remove surrounding quotes if present
                if txt.startswith('"') and txt.endswith('"'):
                    txt = txt[1:-1]
                call = ast.Expr(value=ast.Call(func=ast.Name(id='print', ctx=ast.Load()),
                                                args=[ast.Constant(value=txt)], keywords=[]))
                stmts.append(call)
            else:
                raise ValueError('Unsupported @print syntax')
            i += 1
        elif line.startswith('@for'):
            # @for var i in range<num<a>, num<b>> { ... }
            header = line[len('@for'):].strip()
            # extract variable name and range bounds
            # format: var i in range<num<a>, num<b>> {
            header = header.rstrip('{').strip()
            parts = header.split()
            # expected: ['var', 'i', 'in', 'range<num<a>,', 'num<b>>']
            var_name = parts[1]
            range_part = ' '.join(parts[3:])
            # extract a and b
            a_part = range_part.split('num<')[1].split('>')[0]
            b_part = range_part.split('num<')[2].split('>')[0]
            a = int(a_part)
            b = int(b_part)
            # collect block until matching '}'
            i += 1
            block_lines = []
            while i < len(lines) and not lines[i].startswith('}'):
                block_lines.append(lines[i])
                i += 1
            # skip the closing '}'
            i += 1
            # recursively parse block lines
            block_src = '\n'.join(block_lines)
            body = parse_lamague(block_src)
            for_node = ast.For(target=ast.Name(id=var_name, ctx=ast.Store()),
                               iter=ast.Call(func=ast.Name(id='range', ctx=ast.Load()),
                                             args=[ast.Constant(value=a), ast.Constant(value=b)],
                                             keywords=[]),
                               body=body,
                               orelse=[])
            stmts.append(for_node)
        elif line.startswith('@if'):
            # Very limited: expects condition like i % num<2> == num<0>
            cond_part = line[len('@if'):].strip().rstrip('{').strip()
            # Replace LAMAGUE ops with Python equivalents
            py_cond = cond_part.replace('%', '%').replace('num<', '').replace('>', '')
            # collect block
            i += 1
            block_lines = []
            while i < len(lines) and not lines[i].startswith('}'):
                block_lines.append(lines[i])
                i += 1
            i += 1  # skip '}'
            body = parse_lamague('\n'.join(block_lines))
            if_node = ast.If(test=ast.parse(py_cond, mode='eval').body,
                             body=body,
                             orelse=[])
            stmts.append(if_node)
        else:
            raise ValueError(f'Unsupported line: {line}')
    return stmts


def transpile_and_run(lamague_path: str):
    with open(lamague_path, 'r') as f:
        src = f.read()
    stmts = parse_lamague(src)
    module = ast.Module(body=stmts, type_ignores=[])
    code = compile(module, filename='<lamague>', mode='exec')
    exec(code, {})

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python lamague_demo.py <file.lamague>')
        sys.exit(1)
    transpile_and_run(sys.argv[1])
