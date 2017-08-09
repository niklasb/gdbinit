#!/bin/bash
ln -s ~/gdbinit/gdbinit ~/.gdbinit || exit 1
git submodule update --init || exit 1
