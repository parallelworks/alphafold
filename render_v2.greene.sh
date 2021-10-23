module load vmd/1.9.3
module load imagemagick/intel/7.0.10

on_gcp=$(hostname |grep gcp)

if [ ! -z "$on_gcp" ];then
    template=render_template.gce.tcl
else
    template=render_template.tcl
fi

pdbfile=$1
if [ ! -e "$pdbfile" ];then
	echo "Invalid pdb file"
	echo "Usage: $0 pdb_file"
	exit 1
fi

prefix=$(dirname $pdbfile)/$(basename $pdbfile .pdb)
sed -e "s,_PDBFILE_,$pdbfile," -e "s,_PREFIX_,$prefix," $template.tcl > render.tcl
vmd -dispdev none -e render.tcl -args $pdbfile
convert $prefix.dat.tga $prefix.jpg
\rm $prefix.dat $prefix.dat.tga
