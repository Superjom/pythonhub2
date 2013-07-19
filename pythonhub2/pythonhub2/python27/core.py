# -*- coding: utf-8 -*-
'''
Created on Jul 9, 2013

@author: Chunwei Yan @ pkusz
@mail:  yanchunwei@outlook.com
'''
import sys
import re

class CodinError(Exception):
    def __init__(self, msg):
        self.msg = msg


class CurCodeRuntimeError(CodinError):
    def __init__(self, msg):
        CodinError.__init__(self, msg)
        self.msg = msg


class BufferLengthError(CodinError):
    def __init__(self, msg):
        CodinError.__init__(self, msg)
        self.msg = msg


class CompileError(CodinError):
    def __init__(self, msg):
        CodinError.__init__(self, msg)
        self.msg = msg


class EmptyBuffer(object):
    """
    Write nothing

    used to clean former lines of code
    """
    def write(self, strr):
        pass

    def flush(self):
        pass


class MyBuffer(object):
    SINGLE_MAX_LEN = 70
    MAX_BUFFER_LEN = 200

    def __init__(self):
        self._buffers = []

    def write(self, strr):
        if len(strr) > self.SINGLE_MAX_LEN:
            raise BufferLengthError("Error: single line too long")
        elif len(self._buffers) > self.MAX_BUFFER_LEN:
            raise BufferLengthError("Error: buffer is too long")
        self._buffers.append(strr)

    def flush(self):
        pass

    def clean(self):
        del self._buffers[:]
    
    @property
    def buffer(self):
        return ''.join(self._buffers)


BLOCKED_BUILTINS = (
    'reload', 'open', 'compile', 
    'file', 'eval', 'exec', 'execfile',
    'exit', 'quit', 'help', 'dir',
    'globals', 'locals', 'vars',
)

IGNORE_VARS = set((
    '__builtins__', '__name__', '__exception__',
    '__doc__', '__package__',
))

LEGEL_MODULES = (
    "math", 'random', 'datetime',
    'functools', 'operator', 'string',
    'colletions', 're', 'json',
    'heapq', 'bisect',
)

class Simulator(object):
    """ compile string and run code safely on a server """
    env_gloa = dict(globals().items())
    limited_time = 1

    def __init__(self):
        self.mybuffer = MyBuffer()
        self.emptybuffer = EmptyBuffer()
        self.prepare()

    def prepare(self):
        """ clean the environment """
        self._clean_env()
        self._resert_env()

    def _clean_env(self):
        for name in IGNORE_VARS:
            try:
                del self.env_gloa[name]
            except:
                pass
        for func in  BLOCKED_BUILTINS:
            try:
                delattr(self.env_gloa['__builtins__'], func)
            except:
                pass

    def _resert_env(self):
        _stdout = sys.stdout
        self.env_gloa['mybuffer'] = self.mybuffer
        self.env_gloa['emptybuffer'] = self.emptybuffer
        self.env_gloa['_stdout'] = _stdout
        self.env_gloa['mybuffer'].clean()

        def self_open(*args, **kwargs):
            raise Exception, "Error: don't support open files. "
        self.env_gloa['open'] = self_open
        self.env_gloa['file'] = self_open

    def _detect__illegal_import(self, strr):
        imports = {
                'simple': r"^import\s+(?P<module>[a-zA-Z_]*)",
                'complex': r"^from\s+(?P<module>[a-zA-Z_]*)\s+import\s+(?P<sub_modules>[a-zA-Z_,]*)",
                'func': r"__import__\s*[(]\s*(?P<module>[a-zA-Z_]*)", }
        module = ""
        for key, value in imports.items():
            imports[key] = re.compile(value)
        for key, reg in imports.items():
            try:
                module = reg.search(strr).groups('module')
            except:
                pass
        #if module: print 'import module: ', module[0]
        if module and module[0] not in LEGEL_MODULES:
            return True
        return False

    def run(self, curcode, formercode="", mode='exec'):
        """
        Environment is stored in formercode
        IO buffer will be stored when the current line code runs
        but not the former
        """
        self.env_reset()
        if self.detect_illegal_import(curcode):
            raise CodinError("Error: illegal import")
        # generate code
        code = '\n'.join([ 
            # empty buffer
            "sys.stdout = emptybuffer",
            formercode,
            "sys.stdout = mybuffer",
            curcode,
            "sys.stdout = _stdout", ])

        try:
            comppiled_obj = compile(code, '<string>', mode) 
        except SyntaxError, e:
            raise CompileError(e)
        except Exception, e:
            raise CompileError(e)

        exec comppiled_obj in self.env_gloa

        # resume stdout
        return self.mybuffer.buffer

    def detect_illegal_import(self, strr):
        imports = {
                'simple': r"^import\s+(?P<module>[a-zA-Z_]*)",
                'complex': r"^from\s+(?P<module>[a-zA-Z_]*)\s+import\s+(?P<sub_modules>[a-zA-Z_,]*)",
                'func': r"__import__\s*[(]\s*(?P<module>[a-zA-Z_]*)", }
        module = ""
        for key, value in imports.items():
            imports[key] = re.compile(value)
        for key, reg in imports.items():
            try:
                module = reg.search(strr).groups('module')
            except:
                pass
        #if module: print 'import module: ', module[0]
        if module and module[0] not in LEGEL_MODULES:
            return True
        return False

    def __call__(self, curcode, formercode, mode='exec'):
        return self.run(curcode, formercode, mode)
