#!/bin/bash

ITERATIONS=1

for j in quic h2 h1
do
	python main.py $j lte $ITERATIONS
done

Rscript plots.R lte plt_box
Rscript plots.R lte dom_box
Rscript plots.R lte plt_cum
Rscript plots.R lte dom_box
Rscript plots.R lte plt_init
Rscript plots.R lte plt_minusinit

