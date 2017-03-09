from os import path
import sys

def base_options_C(opt):
    opt.load('compiler_c compiler_cxx')
    opt.add_option('--sys', help='system prefix path for searching requirments')

def base_configure_C(conf):
    conf.load('compiler_c compiler_cxx')
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

def bld_shlib(bld, **kws):
    if sys.platform == 'win32':
        if 'vnum' in kws:
            kws.pop('vnum')
        if 'cnum' in kws:
            kws.pop('cnum')
        if bld.env.get('WIN_STATIC', False):
            bld.stlib(**kws)
            return

    if 'install_path' not in kws:
        kws['install_path'] = '${PREFIX}/lib'
    bld.shlib(**kws)
