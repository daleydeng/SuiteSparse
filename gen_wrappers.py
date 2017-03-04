#!/usr/bin/env python
from os import makedirs, path
from shutil import copyfile
from glob import glob

base_d = 'src'
out_d = 'SourceWrappers'

wrapper_tpl0 = "#include <{inc}>"

wrapper_tpl = """
#define {define}
#include <{inc}>
"""

wrapper_tpl2 = """{defines}
#include <{inc}>
"""

ncwrapper_tpl2 = """
#ifndef NCOMPLEX
{defines}
#include <{inc}>
#endif
"""

scan_dic = {
    'CHOLMOD': ['Check', 'Core', 'Cholesky', 'Partition', 'MatrixOps', 'Modify', 'Supernodal'],
}

def_dic = {
    'CXSparse': {'l': 'CS_LONG', 'c': 'CS_COMPLEX'},
    'KLU': {'l': 'DLONG', 'c': 'COMPLEX'},
    'LDL': {'l': 'LDL_LONG'},
    'RBio': {'i': 'INT'},
    'UMFPACK': {'di': 'DINT', 'dl': 'DLONG', 'ci': 'ZINT', 'cl': 'ZLONG'},
    'CHOLMOD': {'l': 'DLONG'},
}

expand_files_dic = {
    'CHOLMOD': ['cholmod_super_solve', 'cholmod_version'],
    'UMFPACK': ['umf_mem_alloc_head_block', 'umf_mem_alloc_tail_block', 'umf_tuple_lengths', 'umf_mem_free_tail_block', 'umfpack_free_numeric', 'umfpack_free_symbolic', 'umf_transpose', 'umf_symbolic_usage', 'umf_set_stats', 'umf_valid_numeric', 'umf_valid_symbolic', 'umf_mem_init_memoryspace', 'umf_kernel', 'umf_build_tuples'],
}

# src: defines, suffix, is_expand
map_files_dic = {
    'UMFPACK': {
        'umf_ltsolve': ['CONJUGATE_SOLVE', 'conj', True],
        'umf_utsolve': ['CONJUGATE_SOLVE', 'conj', True],
        'umf_triplet': [
            ['DO_MAP', 'map_nox', True],
            ['DO_VALUES', 'nomap_x', True],
            [['DO_MAP', 'DO_VALUES'], 'map_x', True],
        ],
        'umf_assemble': ['FIXQ', 'fixq', True],
        'umf_store_lu': ['DROP', 'drop', True],
        'umfpack_solve': ['WSOLVE', 'w', True],
    }
}

cc_ext_mods = {}

skip_files_dic = {
    'UMFPACK': ['umf_multicompile'],
    'CXSparse': ['cs_convert'],
}

def file_name(f):
    return path.splitext(path.basename(f))[0]

def do_map_file(inc_f, defs, dst_f, mod_defs):
    if type(defs) == str:
        defs = [defs]
    cext = path.splitext(dst_f)[-1]
    if mod_defs:
        dst_fname = path.splitext(dst_f)[0]
        for k, v in mod_defs.items():
            if type(v) == str:
                v = [v]
            defs1 = defs + v
            defines = '\n'.join(['#define '+i for i in defs1])
            dst_f = dst_fname+'_'+k+cext
            open(dst_f, 'w').write(wrapper_tpl2.format(defines=defines, inc=inc_f))
    else:
        defines = '\n'.join(['#define '+i for i in defs])
        open(dst_f, 'w').write(wrapper_tpl2.format(defines=defines, inc=inc_f))

if __name__ == "__main__":
    makedirs(out_d, exist_ok=True)
    for mod in ['AMD', 'BTF', 'CAMD', 'CCOLAMD', 'CHOLMOD', 'COLAMD', 'CXSparse', 'KLU', 'LDL', 'RBio', 'UMFPACK']:
        scan_dirs = scan_dic.get(mod, ['Source'])
        mod_defs = def_dic.get(mod, {'l': 'DLONG', 'i': 'DINT'})
        expand_files = expand_files_dic.get(mod, [])
        map_files = map_files_dic.get(mod, {})
        skip_files = skip_files_dic.get(mod, [])
        cext = '.cc' if mod in cc_ext_mods else '.c'
        for scan_d in scan_dirs:
            srcs = glob(base_d+'/'+mod+'/'+scan_d+'/*.c')
            if mod == 'CHOLMOD':
                srcs = [i for i in srcs if not path.basename(i).startswith('t_')]
            srcs = [i for i in srcs if file_name(i) not in skip_files]

            makedirs(out_d+'/'+mod, exist_ok=True)
            p = out_d+'/'+mod
            inc_d = mod+'/'+scan_d

            for f in srcs:
                fname = file_name(f)
                inc_f = inc_d+'/'+path.basename(f)
                if fname not in map_files:
                    continue
                cfgs = map_files[fname]
                if type(cfgs[-1]) == bool:
                    cfgs = [cfgs]
                for cfg in cfgs:
                    defs, suffix, is_expand = cfg
                    do_map_file(inc_f, defs, p+'/'+fname+'_'+suffix+cext, mod_defs if is_expand else {})

            for f in srcs:
                content = open(f).read()
                fname = file_name(f)
                inc_f = inc_d+'/'+path.basename(f)
                if mod == 'KLU':
                    if all(i not in content for i in ['Entry ', 'Entry)']):
                        for tp in ['i', 'l']:
                            out_f = p+'/'+fname+'_'+tp+cext
                            defines = []
                            if tp == 'l':
                                defines += ['#define '+mod_defs[tp]]
                            out_content = wrapper_tpl2.format(defines='\n'.join(defines), inc=inc_f)
                            open(out_f, 'w').write(out_content)
                    else:
                        for tp0 in ['i', 'l']:
                            for tp1 in ['d', 'c']:
                                out_f = p+'/'+fname+'_'+tp1+tp0+cext
                                defines = []
                                if tp0 == 'l':
                                    defines += ['#define '+mod_defs[tp0]]
                                if tp1 == 'c':
                                    defines += ['#define '+mod_defs[tp1]]
                                out_content = wrapper_tpl2.format(defines='\n'.join(defines), inc=inc_f)
                                open(out_f, 'w').write(out_content)

                elif mod == 'CXSparse':
                    for tp0 in ['i', 'l']:
                        for tp1 in ['d', 'c']:
                            out_f = p+'/'+fname+'_'+tp1+tp0+cext
                            defines = []
                            if tp0 == 'l':
                                defines += ['#define '+mod_defs[tp0]]
                            if tp1 == 'c':
                                defines += ['#define '+mod_defs[tp1]]
                            tpl = ncwrapper_tpl2 if tp1 == 'c' else wrapper_tpl2
                            out_content = tpl.format(defines='\n'.join(defines), inc=inc_f)
                            open(out_f, 'w').write(out_content)


                elif mod in ('UMFPACK',):
                    if all(i not in content for i in ['Entry ', 'Entry)', 'Int ', 'Int)']) and fname not in expand_files:
                        out_f = p+'/'+fname+cext
                        open(out_f, 'w').write(wrapper_tpl0.format(inc=inc_f))
                    else:
                        defs1 = mod_defs.copy()
                        if all(i not in content for i in ['Entry ', 'Entry)']) and fname not in expand_files:
                            del defs1['ci']
                            del defs1['cl']

                        for i, v in defs1.items():
                            out_f = p + '/' + fname+'_'+i+cext
                            out_content = wrapper_tpl.format(define=v, inc=inc_f)
                            open(out_f, 'w').write(out_content)

                else:
                    if any(i in content for i in ['Int ', 'Int)', mod+'_info', mod.lower()+'_info', mod+'_error', mod.lower()+'_error', mod+'_int ', mod+'_int)']) or fname in expand_files:

                        for tp in ['i', 'l']:
                            if tp in mod_defs:
                                out_f = p+'/'+fname+'_'+tp+cext
                                out_content = wrapper_tpl.format(define=mod_defs[tp], inc=inc_f)
                                open(out_f, 'w').write(out_content)
                            else:
                                out_f = p+'/'+fname+'_'+tp+cext
                                open(out_f, 'w').write(wrapper_tpl0.format(inc=inc_f))

                    else:
                        out_f = p+'/'+fname+cext
                        open(out_f, 'w').write(wrapper_tpl0.format(inc=inc_f))
