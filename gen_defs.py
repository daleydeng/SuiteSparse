#!/usr/bin/env python
import os

base_d = 'src'
out_d = 'defs'

clang_ast = "clang -Xclang -ast-dump -fsyntax-only {} > {}"

def gen_ast(headers, out_f, incs=[]):
    if type(headers) == str:
        headers = [headers]
    inc = ' '.join('-I'+i for i in incs)
    for f in headers:
        cmd = clang_ast.format(inc+' '+f, out_f)
        os.system(cmd)

def extract_funcs(ast_f):
    funcs = []
    for l in open(ast_f):
        if 'FunctionDecl' not in l:
            continue

        prefixs = prefixs_dic.get(mod, [mod+'_'])
        if type(prefixs) == str:
            prefixs = [prefixs]

        for prefix in prefixs:
            func_name = l.split()[5]
            if func_name.startswith(prefix):
                funcs.append(func_name)
    return funcs

exports_dic = {
    'suitesparseconfig': ['SuiteSparse_config'],
}

def_tpl = """LIBRARY {}.dll
EXPORTS
{}
"""

prefixs_dic = {
    'suitesparseconfig': 'SuiteSparse_',
    'cxsparse': 'cs_',
    'umfpack': ['umf_', 'umfpack_'],
}

if __name__ == "__main__":
    os.makedirs(out_d, exist_ok=True)
    mod = 'suitesparseconfig'
    ast_f = out_d+'/'+mod+'.ast'
    gen_ast(base_d+'/SuiteSparse_config/SuiteSparse_config.h', ast_f, incs=['src/SuiteSparse_config'])
    funcs = extract_funcs(ast_f)
    funcs += exports_dic.get(mod, [])
    open(out_d+'/'+mod+'.def', 'w').write(def_tpl.format(mod, '\n'.join(funcs)))

    for i in ['AMD', 'BTF', 'CAMD', 'COLAMD', 'CCOLAMD', 'CHOLMOD', ('CXSparse', 'cs'), 'KLU', 'LDL', 'UMFPACK']:
        if type(i) == str:
            h = i.lower()
        else:
            i, h = i
        mod = i.lower()
        ast_f = out_d+'/'+mod+'.ast'
        gen_ast(base_d+'/{}/Include/{}.h'.format(i, h), ast_f, incs=['src/SuiteSparse_config', 'src/AMD/Include', 'src/COLAMD/Include', 'src/BTF/Include'])
        funcs = extract_funcs(ast_f)
        funcs += exports_dic.get(mod, [])
        open(out_d+'/'+mod+'.def', 'w').write(def_tpl.format(mod, '\n'.join(funcs)))
