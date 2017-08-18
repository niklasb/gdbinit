set disassembly-flavor intel

define hook-quit
  set confirm off
end

source ~/gdbinit/binbase.py
source ~/gdbinit/heap.py

define peda
source ~/gdbinit/load_peda.py
end
