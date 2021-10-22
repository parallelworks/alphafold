module load vmd/1.9.3
module load imagemagick/intel/7.0.10

pdbfile=$1
if [ ! -e "$pdbfile" ];then
	echo "Invalid pdb file"
	echo "Usage: $0 pdb_file"
	exit 1
fi

prefix=$(dirname $pdbfile)/$(basename $pdbfile .pdb)
sed -e "s,_PDBFILE_,$pdbfile," -e "s,_PREFIX_,$prefix," render_template.tcl > render.tcl
vmd -dispdev none -e render.tcl -args $pdbfile
convert $prefix.dat.tga $prefix.jpg
\rm $prefix.dat $prefix.dat.tga
