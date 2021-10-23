#!/bin/bash
scriptdir=/home/hocky/alphafold-setup
args=''
for i in "$@"; do
    i="${i//\\/\\\\}"
    args="$args \"${i//\"/\\\"}\""
done

if [ "$SLURM_TMPDIR" != "" ]; then
    bind="--bind $SLURM_TMPDIR:/tmp"
fi

singularity exec --nv $bind \
            --bind $scriptdir/params:/tmp/params:ro \
            --overlay $scriptdir/alphafold-20210721-cuda11.2.2-cudnn8-devel-ubuntu20.04.sqf:ro \
            --overlay $scriptdir/alphafold-deps-cuda11.2.2-cudnn8-devel-ubuntu20.04.sqf:ro \
            $scriptdir/cuda11.2.2-cudnn8-devel-ubuntu20.04.sif \
            /bin/bash -c "
source /ext3/env.sh;
cd /tmp;
ln -sf /ext3/alphafold;
cd -;
ln -s /tmp/params;
$args
\rm /tmp/alphafold
"
