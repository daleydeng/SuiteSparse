from glob import glob
import re
from os import path
import sys

def options(opt):
    opt.load('compiler_c')
    opt.add_option('--sys', help='system prefix path for searching requirments')

def configure(conf):
    conf.load('compiler_c')
    env = conf.env
    sys_prefix = conf.options.sys
    if sys_prefix:
        inc_path = sys_prefix+'/include'
        env.prepend_value('CFLAGS', '-I'+inc_path)
        env.prepend_value('CXXFLAGS', '-I'+inc_path)
        libpath = [sys_prefix+'/lib', sys_prefix+'/lib64']
        env.prepend_value('LIBPATH', libpath)

    if not conf.options.out:
        conf.options.out = 'build'
    env.append_value('RPATH', path.realpath(conf.options.out))

    if sys.platform != 'win32':
        conf.check_cc(lib='m', uselib_store='m')
        env.append_value('LINKFLAGS_cshlib', ["-Wl,--unresolved-symbols=ignore-in-shared-libs", "-Wl,--as-needed"])
    else:
        # _Complex in C99 not supported by msvc
        env.append_value('DEFINES', 'NCOMPLEX=1')

    conf.check_cc(lib='metis', uselib_store='metis')
    conf.check_cc(lib='openblas', uselib_store='openblas')

version_files = {
    'suitesparseconfig': 'SuiteSparse_config/Makefile',
}

def extract_suitesparse_version(base_d):
    versions = {}
    for mod in ['suitesparseconfig', 'AMD', 'BTF', 'CAMD', 'CCOLAMD', 'COLAMD', 'CHOLMOD', 'CXSparse', 'LDL', 'KLU', 'UMFPACK', 'RBio']:
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

def bld_shlib(bld, **kws):
    if sys.platform == 'win32':
        if 'vnum' in kws:
            kws.pop('vnum')
        if 'cnum' in kws:
            kws.pop('cnum')
    bld.shlib(**kws)

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
