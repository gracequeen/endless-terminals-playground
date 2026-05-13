#!/bin/bash
# Auto-generated solve script
set -e

cat /home/user/optim/cplex.prm
sed -i 's/CPXPARAM_MIP_Tolerances_MIPGap 0.01/CPXPARAM_MIP_Tolerances_MIPGap 0.001/' /home/user/optim/cplex.prm
cat /home/user/optim/cplex.prm
