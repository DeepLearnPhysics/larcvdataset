#!/bin/sh

# setups environment variables for larcvdataset, an additional wrapper to larcv::ThreadFiller
# assumes script called in the folder code sits

# clean up previously set env
if [[ -z $FORCE_LARCVDATASET_BASEDIR ]]; then
    where="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    export LARCVDATASET_BASEDIR=${where}
else
    export LARCVDATASET_BASEDIR=$FORCE_LARCVDATASET_BASEDIR
fi

# Add to python path
[[ ":$PYTHONPATH:" != *":${LARCVDATASET_BASEDIR}:"* ]] && PYTHONPATH="${LARCVDATASET_BASEDIR}:${PYTHONPATH}"
# Add to ld library path
[[ ":$LD_LIBRARY_PATH:" != *":${LARCVDATASET_BASEDIR}/lib:"* ]] && LD_LIBRARY_PATH="${LARCVDATASET_BASEDIR}/lib:${LD_LIBRARY_PATH}"
