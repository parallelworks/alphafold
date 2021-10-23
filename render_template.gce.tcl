#mol new predictions/alphafold_1ubq/1ubq_relaxed_model_1_seed1.pdb waitfor all

############################################################################
#cr
#cr            (C) Copyright 1995-2007 The Board of Trustees of the
#cr                        University of Illinois
#cr                         All Rights Reserved
#cr
############################################################################

############################################################################
# RCS INFORMATION:
#
#       $RCSfile: .vmdrc,v $
#       $Author: johns $        $Locker:  $                $State: Exp $
#       $Revision: 1.9 $      $Date: 2007/01/12 20:12:44 $
#
############################################################################
# DESCRIPTION:
#
# VMD startup script.  The commands here are executed as soon as VMD starts up
############################################################################

# turn on lights 0 and 1
light 0 on
light 1 on
light 2 off
light 3 off

# position the stage and axes
axes location off
stage location off

# start the scene a-rockin'
#rock y by 1

# User's default values for newly loaded molecules/reps, etc
mol default color Name
mol default style {NewCartoon 0.300000 15.000000 4.100000 0}
mol default selection protein
mol default material Opaque

# change background color
color Display Background white
color Display FPS black
color Axes Labels black

#set pdbfile [lindex $argv 0]
set pdbfile _PDBFILE_
puts "Loading pdb file: $pdbfile"
mol new $pdbfile waitfor all
puts "Here 1"
#display resize 800 800
puts "Here 2"
display resetview
puts "Here 3"
scale by 2

#set namelength [string length $pdbfile]
#set prefix [string range $pdbfile 0 [expr $namelength - 5]]
#set prefix [file dirname $pdbfile]/[file rootname [file tail $pdbfile]]
set prefix _PREFIX_
puts "Rendering to $prefix"
puts "Running - render Tachyon ${prefix}.dat '/usr/local/lib/vmd/tachyon_LINUXAMD64' -aasamples 12 %s -format TARGA -res 800 800 -o %s.tga"
render Tachyon ${prefix}.dat "/usr/local/lib/vmd/tachyon_LINUXAMD64" -aasamples 12 %s -format TARGA -res 800 800 -o %s.tga
sleep 1
exit
