set disassembly-flavor intel

define hook-quit
  set confirm off
end

source ~/gdbinit/binbase.py
source ~/gdbinit/heap.py

define peda
  source ~/gdbinit/load_peda.py
end

define tcp
  file socat
  catch exec
  set follow-fork-mode child
  r tcp4-l:$arg0,bind=127.0.0.1,reuseaddr exec:$arg1,sigint,stderr
end

set history filename ~/.gdb_history
set history save on
set history size 100000
set history remove-duplicates 10
