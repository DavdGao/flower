#!/bin/bash

set -e

conda activate flower

for i in {1..${1}}
do
  python client_batch.py &
done

wait

echo "Done!"
