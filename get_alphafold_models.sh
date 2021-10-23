#!/bin/bash
#SBATCH --job-name get_af_models
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --tasks-per-node 1
#SBATCH --cpus-per-task 8
#SBATCH --mem 30GB
#SBATCH -t 8:00:00

on_gcp=$(hostname |grep gcp)

if [ -z "$runscript" ];then
    if [ ! -z "$on_gcp" ];then
        runscript=./run-alphafold-gce.sh
    else
        runscript=./run-alphafold-20210721.sh
    fi
fi

if [ -z "$fasta_file" ];then
    echo "Setting fasta_file to $1..."
    fasta_file=$(realpath $1)
    seed=$2
fi

if [ -z "$seed" ];then
    seed=1
fi

if [ -z "$fasta_file" ];then
    echo "Usage: $0 fasta_file or sbatch --export fasta_file=FASTA_FILE $0"
    exit
fi

mkdir predictions

get_out_dir () {
    fasta_file=$1
    echo $(dirname $fasta_file)/alphafold_$(basename $fasta_file .fasta)
}

#debug version
out_dir=$(get_out_dir $fasta_file)
if [ -d $out_dir ];then
    echo "Skipping $fasta_file b/c already present"
else
   bash $runscript python ./run_alphafold_fastalign_homooligomer_nseed.py --seed $seed --n_models 5 --use_amber $fasta_file
fi

mv $out_dir predictions/

exit

out_dir=$(get_out_dir $fasta_file)
if [ -d $out_dir ];then
    echo "skipping $fasta_file "
else
   bash $runscript python ./run_alphafold_fastalign_homooligomer_nseed.py --seed $seed --use_amber $fasta_file
fi

mv $out_dir predictions/

out_dir=$(get_out_dir $fasta_file)_noMSA
if [ -d $out_dir ];then
   echo "skipping $fasta_file no-msa"
else
   bash $runscript python ./run_alphafold_fastalign_homooligomer_nseed.py --seed $seed --use_amber $fasta_file --no_msa
fi

mv $out_dir predictions/

