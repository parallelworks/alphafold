#!/bin/bash

args=''
for i in "$@"; do 
    i="${i//\\/\\\\}"
    args="$args \"${i//\"/\\\"}\""
done

if [[ "$(hostname -s)" =~ ^g[r,v] ]]; then nv="--nv"; fi

if [ "$SLURM_TMPDIR" != "" ]; then
    bind="--bind $SLURM_TMPDIR:/tmp"
fi

ln -sf /alphafold-data/params
ln -sf /ext3/alphafold/alphafold
singularity exec $nv $bind \
	    --bind /vast/work/public/alphafold:/alphafold-data:ro \
	    --overlay /scratch/work/public/singularity/alphafold-20210721-cuda11.2.2-cudnn8-devel-ubuntu20.04.sqf:ro \
	    --overlay /scratch/work/public/singularity/alphafold-deps-cuda11.2.2-cudnn8-devel-ubuntu20.04.sqf:ro \
	    /scratch/work/public/singularity/cuda11.2.2-cudnn8-devel-ubuntu20.04.sif \
	    /bin/bash -c "
source /ext3/env.sh; 
$args
"

#python -u run_alphafold.py $args
#--overlay /vast/work/public/alphafold/alphafold-data.sqf:ro \
