# brutal hack for __file__ not working properly in gdb
__file__ = '~/gdbinit/peda/peda.py'
gdb.execute('source %s'%__file__)
gdb.execute('pset option clearscr off')
