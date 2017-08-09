"""trace allocations"""

import gdb

def p(x):
    # output hex/dec is apparently configurable because it differs under PEDA
    res = str(gdb.parse_and_eval(x))
    if res.startswith('0x'):
        return int(res, 16)
    else:
        return int(res)

def is64():
    return p('sizeof(void*)') == 8

class HeapFinishBreakpoint(gdb.FinishBreakpoint):
    def __init__(self, tracer, fn_name, args):
        super(HeapFinishBreakpoint, self).__init__(internal=True)
        self._tracer = tracer
        self._fn_name = fn_name
        self._args = args
    def stop (self):
        return_value = None
        if self._fn_name != 'free':
            return_value = p('$rax') if is64() else p('$eax')
        self._tracer.trace(self._fn_name, self._args, return_value)
        return False
    def out_of_scope(self):
        #gdb.write("abnormal finish {}\n".format(self._count))
        pass

class HeapBreakpoint(gdb.Breakpoint):
    def __init__(self, tracer, fn_name):
        super(HeapBreakpoint, self).__init__(fn_name, internal=True)
        self._tracer = tracer
        self._fn_name = fn_name
        self._finish_bp = None
        if fn_name in ['malloc', 'free']:
            self._arg_cnt = 1
        else:
            self._arg_cnt = 2
    def stop(self):
        args = []
        if self._arg_cnt > 0:
            if is64():
                args.append(p('$rdi'))
            else:
                args.append(p('*(unsigned int*)($esp+4)'))
        if self._arg_cnt > 1:
            if is64:
                args.append(p('$rsi'))
            else:
                args.append(p('*(unsigned int*)($esp+8)'))
        self._finish_bp = HeapFinishBreakpoint(self._tracer, self._fn_name,
                args)
        return False

class HeapTracer(object):
    def __init__(self):
        super(HeapTracer, self).__init__()

    def trace(self, fn_name, args, ret_val):
        args = ', '.join('0x%x' % arg for arg in args)
        if ret_val is not None:
            gdb.write('{}({}) = 0x{:x}\n'.format(fn_name, args, ret_val))
        else:
            gdb.write('{}({})\n'.format(fn_name, args))

class HeapTracing(gdb.Command):
    def __init__(self):
        super(HeapTracing, self).__init__('heap-tracing-enable',
                gdb.COMMAND_TRACEPOINTS)
        self._enabled = False
        self._tracer = HeapTracer()
        self._breakpoints = []
    def invoke(self, argument, from_tty):
        if self._enabled:
            raise Exception('Heap tracing already enabled')
        for fn_name in ['malloc', 'calloc', 'realloc', 'free']:
            self._breakpoints.append(HeapBreakpoint(self._tracer, fn_name))

HeapTracing()
