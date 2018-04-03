from contextlib import contextmanager
import subprocess
import sys


@contextmanager
def add_sys_paths(paths):
    """Add to sys.path, and revert on scope exit.
    """
    original_syspath = sys.path[:]
    sys.path.extend(paths)

    try:
        yield
    finally:
        sys.path = original_syspath


def popen(args, **kwargs):
    """Wrapper for `subprocess.Popen`.

    Avoids python bug described here: https://bugs.python.org/issue3905. This
    can arise when apps (maya) install a non-standard stdin handler.
    """

    # avoid non-standard stdin handler
    if "stdin" not in kwargs and sys.stdin.fileno() not in (0, 1, 2):
        kwargs["stdin"] = subprocess.PIPE
    if kwargs.pop('vs_dev_shell', False):
        # hack to make cmake nmake work on windows:
        # https://github.com/nerdvegas/rez/issues/469
        #
        # FIX 1: invert single quotes for double quotes and viceversa to fix:
        # Error:
        # [100%] Generating py/python/hello_world.pyc
        # File "<string>", line 1
        #     'import
        #           ^
        # SyntaxError: EOL while scanning string literal
        # NMAKE : fatal error U1077: 'C:\Python27\python.EXE' : return code '0x1'
        #
        # FIX 2 -- run Visual Studio command prompt before the rest of the rez command to fix:
        # CMake Error at C:/Program Files (x86)/CMake/share/cmake-3.6/Modules/CMakeTestCCompiler.cmake:61 (message):
        #   The C compiler "C:/Program Files (x86)/Microsoft Visual Studio
        #   14.0/VC/bin/cl.exe" is not able to compile a simple test program.
        # AND / OR:
        # -- The CXX compiler identification is unknown
        # CMake Error in CMakeLists.txt:
        #   The CMAKE_C_COMPILER:
        #
        #     cl
        #
        #   is not a full path and was not found in the PATH.
        #
        # Hack should not live for too long!!!
        import os
        cwd = kwargs['cwd']
        for root, dir, files in os.walk(cwd):
            for f in files:
                if f == 'build.make':
                    update_nmake_py_compile(os.path.join(root, f))
        return subprocess.Popen('C:\\WINDOWS\\system32\\cmd.exe /C "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\VC\Auxiliary\\Build\\vcvars64.bat' '"' f' && {args[-1]}',**kwargs)
    return subprocess.Popen(args, **kwargs)


def update_nmake_py_compile(src_file):
    print(f'FIXING {src_file}')
    import re
    # could improve the regex but not caring for now. (elegant hack not a priority and want to break REZ when it has to)
    regex = re.compile(r'import py_compile ; py_compile\.compile \( \"(?P<src>[\w+\/\.\:]+)\", \"(?P<tgt>[\w+\/\.\:]+)\", None, True \)')
    lines = open(src_file).read().splitlines()

    for i, l in enumerate(lines):
        m = regex.search(l)
        if m:
            print(f'UPDATING LINE: {l}')
            src = m.group('src')
            tgt = m.group('tgt')
            new_l = (
f'''
\tpython -c "import py_compile ; py_compile.compile ( '{src}', '{tgt}', None, True ) "
''')
            lines[i] = new_l
            print(f'NEW LINE: {new_l}')
    open(src_file, 'w').write('\n'.join(lines))
