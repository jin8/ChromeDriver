#!/bin/bash

ITERATIONS=1

for j in quic h2 h1
do
	python main.py $j wifi $ITERATIONS
done

Rscript plots.R wifi plt_box
Rscript plots.R wifi dom_box
Rscript plots.R wifi plt_cum
Rscript plots.R wifi dom_box
Rscript plots.R wifi plt_init
Rscript plots.R wifi plt_minusinit
