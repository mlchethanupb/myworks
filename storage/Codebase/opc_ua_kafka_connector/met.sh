#!/bin/bash
diskSpace=$(docker exec -t -i 49394bfbacd0 /bin/sh -c "gluster volume status vol_331392cba7ebacda46a545d968f8d9af detail | grep 'Disk Space Free' | cut -f2 -d":" | head -n1 |sed 's/^ *//g'")
echo "$diskSpace">>c.txt
