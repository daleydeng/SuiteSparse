from glob import glob
import re
from os import path
import sys

def options(opt):
    opt.load('compiler_c')
    opt.add_option('--sys', help='system prefix path for searching requirments')

def configure(conf):
    conf.load('compiler_c')
    sys_prefix = conf.options.sys
    if sys_prefix:
        conf.env.INCLUDES_sys = [sys_prefix+'/include']
        libpath = [sys_prefix+'/lib', sys_prefix+'/lib64']
        conf.env.LIBPATH_sys = libpath
        conf.env.RPATH_sys = libpath
    else:
        if not conf.options.out:
            conf.options.out = 'build'
        conf.env.append_value('RPATH', path.realpath(conf.options.out))

    conf.env.append_value('LINKFLAGS_cshlib', ["-Wl,--unresolved-symbols=ignore-in-shared-libs", "-Wl,--as-needed"])
    if sys.platform != 'win32':
        conf.check_cc(lib='m', use='sys', uselib_store='m')

    conf.check_cc(lib='metis', use='sys', uselib_store='metis')
    conf.check_cc(lib='openblas', use='sys', uselib_store='openblas')

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

def build(bld):
    env = bld.env
    versions = extract_suitesparse_version('src')
    env.append_value('INCLUDES', ['src', 'src/SuiteSparse_config'])

    bld.shlib(source=glob('src/SuiteSparse_config/*.c'), target='suitesparseconfig', use=['m'], vnum=versions['suitesparseconfig'][0])

    mod_deps = {
        'CHOLMOD': ['AMD', 'CAMD', 'CCOLAMD', 'COLAMD', 'openblas', 'metis'],
        'KLU': ['AMD', 'COLAMD', 'BTF'],
        'UMFPACK': ['AMD', 'cholmod'],
    }

    for mod in ['AMD', 'BTF', 'CAMD', 'COLAMD', 'CCOLAMD', 'CHOLMOD', 'CXSparse', 'LDL', 'KLU']:
        deps = mod_deps.get(mod, [])
        lib = [i.lower() for i in deps]
        incs = ['src/'+i+'/Include' for i in deps]
        use = ['suitesparseconfig']+[i.lower() for i in deps]
        if sys.platform != 'win32':
            use.append('m')
        bld.shlib(source=glob('SourceWrappers/'+mod+'/*.c'), target=mod.lower(), includes=['src/'+mod+'/Include']+incs, use=use, vnum=versions[mod][0])
