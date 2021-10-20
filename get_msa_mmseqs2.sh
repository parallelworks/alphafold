#!/bin/bash
#from  https://colab.research.google.com/github/sokrypton/ColabFold/blob/main/verbose/alphafold_noTemplates_noMD.ipynb#scrollTo=i9HtoJxiOK3f
scriptdir=$(cd $(dirname $0);pwd)
fasta=$1
name=$(basename $fasta .fasta)
parse="python $scriptdir/parse_output.py"

if [ ! -e "$fasta" ];then
	echo "Error: fasta file ($fasta) not found"
        echo "Usage: $0 fasta_file"
	exit
fi

cd $(dirname $fasta)
fasta=$(basename $fasta)

#replace jq -r '.FIELD'
#with  $parse '{"id":"EuweJY4nl2GLJN8IUZQfi7W-TTY6-0CkhHW5Nw","status":"COMPLETE"}' status

ID=$(curl -s -F q=@$fasta -F mode=all https://a3m.mmseqs.com/ticket/msa | $parse id)
STATUS=$(curl -s https://a3m.mmseqs.com/ticket/${ID} | $parse status)
echo "Got ticket $ID"
while [ "${STATUS}" == "RUNNING" ]; do
    STATUS=$(curl -s https://a3m.mmseqs.com/ticket/${ID} | $parse status)
    sleep 1
done
if [ "${STATUS}" == "COMPLETE" ]; then
    curl -s https://a3m.mmseqs.com/result/download/${ID}  > $name.tar.gz
    curl -s https://a3m.mmseqs.com/result/${ID}/0 > $name.server_results.txt
    tar xzf $name.tar.gz
    tr -d '\000' < uniref.a3m > $name.a3m
else
    echo "MMseqs2 server did not return a valid result."
    echo "Using original fasta file"
    echo "${STATUS}"
    echo $(curl -s https://a3m.mmseqs.com/ticket/${ID})
    cp $fasta $name.a3m
    exit 1
fi
#echo $(curl -s https://search.mmseqs.com/result/${ID}/0)
echo "Found $(grep -c ">" $name.a3m) sequences (after redundacy filtering)"
