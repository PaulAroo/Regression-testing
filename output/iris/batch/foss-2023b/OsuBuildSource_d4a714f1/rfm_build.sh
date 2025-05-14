#!/bin/bash

_onerror()
{
    exitcode=$?
    echo "-reframe: command \`$BASH_COMMAND' failed (exit code: $exitcode)"
    exit $exitcode
}

trap _onerror ERR

module load env/testing/2023b
module load toolchain/foss/2023b
module load tools/EasyBuild
curl -LJO http://mvapich.cse.ohio-state.edu/download/mvapich/osu-micro-benchmarks-7.2.tar.gz
tar xzf osu-micro-benchmarks-7.2.tar.gz
cd osu-micro-benchmarks-7.2
./configure CC="mpicc" CXX="mpicxx" FC="mpifort"
make -j 8
