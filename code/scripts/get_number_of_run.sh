#!/usr/bin/env bash

if test "$#" -ne 1; then
    echo "Number of required parameter = 2 (scenario and configuration)"
    exit
fi

cd /mnt/iconic/chethan/simulation/CP-CV2X/code/scenarios/InTAS/scenario && /home/thi/mariyaklla/programs/omnetpp-5.7/bin/opp_run_release -n /mnt/iconic/chethan/simulation/CP-CV2X/code/src/artery:/mnt/iconic/chethan/simulation/CP-CV2X/code/src/traci:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/veins/examples/veins:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/veins/src/veins:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/inet/src:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/inet/examples:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/inet/tutorials:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/inet/showcases:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/simulte/simulations:/mnt/iconic/chethan/simulation/CP-CV2X/code/extern/simulte/src -l /mnt/iconic/chethan/simulation/CP-CV2X/code/extern/simulte/out/clang-release/src/liblte.so -l /mnt/iconic/chethan/simulation/CP-CV2X/code/build/src/artery/envmod/libartery_envmod.so -l /mnt/iconic/chethan/simulation/CP-CV2X/code/build/src/artery/storyboard/libartery_storyboard.so -l /mnt/iconic/chethan/simulation/CP-CV2X/code/extern/inet/out/clang-release/src/libINET.so -l /mnt/iconic/chethan/simulation/CP-CV2X/code/extern/veins/out/clang-release/src/libveins.so -l /mnt/iconic/chethan/simulation/CP-CV2X/code/build/src/artery/libartery_core.so omnetpp.ini -f config/$1.ini -c $1 -s -q runnumbers
