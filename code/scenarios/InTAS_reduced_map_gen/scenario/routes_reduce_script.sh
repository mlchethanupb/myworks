 #!/bin/bash

 file_path=/home/momo/dateien/Studies/thesis/workspace/InTAS_reduced/scenario/routes

 for f in $file_path/*
 do
    output_file="$(basename $f)"
    echo "creating file : $output_file"
    python $SUMO_HOME/tools/route/cutRoutes.py ingolstadt_reduced.net.xml $f --routes-output routes_reduced/$output_file --orig-net ingolstadt.net.xml
 done