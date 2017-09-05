"""trace allocations"""

import gdb
import traceback

def p(x):
    # output hex/dec is apparently configurable because it differs under PEDA
    res = str(gdb.parse_and_eval(x))
    if res.startswith('0x'):
        return int(res, 16)
    else:
        return int(res)

def is64():
    return p('sizeof(void*)') == 8

# Sometimes we need *malloc, *free etc. to really break on function entry.
# But other times this doesn't work...
addr = {
    'free': 'free',
    'malloc': 'malloc',
    'calloc': 'calloc',
    'realloc': 'realloc'
}
arg_cnt = {
    'free': 1,
    'malloc': 1,
    'calloc': 2,
    'realloc': 2,
}
does_return = {'malloc', 'calloc', 'realloc'}

def init():
    global get_args, get_retval, get_retaddr
    if is64():
        get_args = [
            lambda: p('$rdi'),
            lambda: p('$rsi'),
        ]
        get_retval = lambda: p('$rax')
        get_retaddr = lambda: p('*(unsigned long*)$rsp')
    else:
        get_args = [
            lambda: p('*(unsigned long*)($esp+{})'.format(i))
            for i in range(4, 9, 4)
        ]
        get_retval = lambda: p('$eax')
        get_retaddr = lambda: p('*(unsigned long*)$esp')

# track recursion level, because we only want to trace the outermost call
in_heap_func = False

class HeapFinishBreakpoint(gdb.Breakpoint):
    def __init__(self, fn_name, retaddr):
        super(HeapFinishBreakpoint, self).__init__('*{}'.format(retaddr), internal=True)
        self._fn_name = fn_name

    def stop(self):
        try:
            global in_heap_func
            in_heap_func = False
            if self._fn_name in does_return:
                gdb.write(' = 0x{:x}\n'.format(get_retval()))
            else:
                gdb.write('\n')
            self.enabled = False
            return False
        except:
            traceback.print_exc()
            raise

class HeapBreakpoint(gdb.Breakpoint):
    def __init__(self, fn_name):
        super(HeapBreakpoint, self).__init__(addr[fn_name], internal=True)
        self._fn_name = fn_name
        self._finish_bp = None
        self._arg_cnt = arg_cnt[self._fn_name]

    def stop(self):
        try:
            global in_heap_func
            if in_heap_func:
                return False
            in_heap_func = True
            args = [get_args[i]() for i in range(self._arg_cnt)]

            gdb.write('{}({})'.format(
                self._fn_name,
                ', '.join('0x{:x}'.format(arg) for arg in args)))

            if self._finish_bp is not None:
                self._finish_bp.delete()
            self._finish_bp = HeapFinishBreakpoint(
                    self._fn_name,
                    retaddr=get_retaddr())
            return False
        except:
            traceback.print_exc()
            raise

class HeapTracing(gdb.Command):
    def __init__(self):
        super(HeapTracing, self).__init__('heap-tracing-enable',
                gdb.COMMAND_TRACEPOINTS)
        self._enabled = False
        self._breakpoints = []

    def invoke(self, argument, from_tty):
        if self._enabled:
            raise Exception('Heap tracing already enabled')
        init()
        for fn_name in addr:
            self._breakpoints.append(HeapBreakpoint(fn_name))

HeapTracing()
