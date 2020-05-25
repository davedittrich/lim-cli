export OS=$(uname -s)
export PYTHONPATH=$(pwd)
export LIM="python3 -m lim --debug"

load 'libs/bats-support/load'
load 'libs/bats-assert/load'


# vim: set ts=4 sw=4 tw=0 et :
