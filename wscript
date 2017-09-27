import os, shutil
copy_files = ['wscript_common.py']
if 'DEEP3D_BASE' in os.environ:
    for i in copy_files:
        src_f = os.environ['DEEP3D_BASE']+'/deep3d/base/'+i
        if not os.path.exists(i) or os.stat(i) < os.stat(src_f):
            shutil.copy2(src_f, '.')

from glob import glob
import re
from os import path
import sys
from wscript_common import base_options_C, base_configure_C, bld_shlib

def options(opt):
    base_options_C(opt)

def configure(conf):
    base_configure_C(conf)
    env = conf.env

    if sys.platform != 'win32':
        conf.check_cc(lib='m', uselib_store='m')
        env.append_value('LINKFLAGS_cshlib', ["-Wl,--unresolved-symbols=ignore-in-shared-libs", "-Wl,--as-needed"])
    else:
        # _Complex in C99 not supported by msvc
        env.append_value('DEFINES', 'NCOMPLEX=1')
        env.WIN_STATIC = True

    conf.check_cc(lib='metis', uselib_store='metis')
    conf.check_cc(lib='openblas', uselib_store='openblas')

version_files = {
    'suitesparseconfig': 'SuiteSparse_config/Makefile',
}

def extract_suitesparse_version(base_d):
    versions = {}
    for mod in ['suitesparseconfig', 'AMD', 'BTF', 'CAMD', 'CCOLAMD', 'COLAMD', 'CHOLMOD', 'CXSparse', 'LDL', 'KLU', 'UMFPACK', 'RBio', 'SPQR']:
        vf = version_files.get(mod, mod+'/Lib/Makefile')
        for l in open(base_d+'/'+vf):
            k, *v = l.split('=')
            k = k.strip()
            if k == 'VERSION':
                version = v[0].strip()
            elif k == 'SO_VERSION':
                so_version = v[0].strip()
                break
        versions[mod] = version, so_version
    return versions

def build(bld):
    env = bld.env
    versions = extract_suitesparse_version('src')
    env.append_value('INCLUDES', ['src', 'src/SuiteSparse_config'])

    mod = 'suitesparseconfig'
    bld_shlib(bld, source=glob('src/SuiteSparse_config/*.c'), target=mod, use=['m'], vnum=versions[mod][0], defs='defs/{}.def'.format(mod))

    mod_deps = {
        'CHOLMOD': ['AMD', 'CAMD', 'CCOLAMD', 'COLAMD', 'openblas', 'metis'],
        'KLU': ['AMD', 'COLAMD', 'BTF'],
        'UMFPACK': ['AMD', 'cholmod'],
    }

    for mod in ['AMD', 'BTF', 'CAMD', 'COLAMD', 'CCOLAMD', 'CHOLMOD', 'CXSparse', 'LDL', 'KLU']:
        deps = mod_deps.get(mod, [])
        lib = [i.lower() for i in deps]
        incs = ['src/'+i+'/Include' for i in deps]
        use = ['m', 'suitesparseconfig']+[i.lower() for i in deps]
        bld_shlib(bld, source=glob('SourceWrappers/'+mod+'/*.c*'), target=mod.lower(), includes=['src/'+mod+'/Include']+incs, use=use, vnum=versions[mod][0], defs='defs/{}.def'.format(mod.lower()))
    headers = [i for i in glob('src/SuiteSparse_config/*.h*')+glob('src/*/Include/*.h*') if i != 'src/CSparse/Include/cs.h']
    bld.install_files('${PREFIX}/include/suitesparse', headers)

    mod = 'SPQR'
    bld_shlib(bld, source=glob('src/{}/Source/*.cpp'.format(mod)), target=mod.lower(), includes=['src/{}/Include'.format(mod), 'src/CHOLMOD/Include'], vnum=versions[mod][0])
    mod = 'RBio'
    bld_shlib(bld, source=glob('src/{}/Source/*.c'.format(mod)), target=mod.lower(), includes=['src/{}/Include'.format(mod)], use=['suitesparseconfig'], vnum=versions[mod][0])
