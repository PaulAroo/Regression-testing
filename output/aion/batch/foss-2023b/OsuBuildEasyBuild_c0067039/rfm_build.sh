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
cp /mnt/aiongpfs/users/paromolaran/project_playground/reframe_tests/OSU-Micro-Benchmarks-7.2-foss-2023b.eb /mnt/aiongpfs/users/paromolaran/project_playground/stage/aion/batch/foss-2023b/OsuBuildEasyBuild_c0067039/
export EASYBUILD_BUILDPATH=/mnt/aiongpfs/users/paromolaran/project_playground/stage/aion/batch/foss-2023b/OsuBuildEasyBuild_c0067039/easybuild/build
export EASYBUILD_INSTALLPATH=/mnt/aiongpfs/users/paromolaran/project_playground/stage/aion/batch/foss-2023b/OsuBuildEasyBuild_c0067039/easybuild
export EASYBUILD_PREFIX=/mnt/aiongpfs/users/paromolaran/project_playground/stage/aion/batch/foss-2023b/OsuBuildEasyBuild_c0067039/easybuild
export EASYBUILD_SOURCEPATH=/mnt/aiongpfs/users/paromolaran/project_playground/stage/aion/batch/foss-2023b/OsuBuildEasyBuild_c0067039/easybuild
eb OSU-Micro-Benchmarks-7.2-foss-2023b.eb -f --detect-loaded-modules=purge
