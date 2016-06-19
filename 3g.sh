#!/bin/bash

ITERATIONS=1

for j in quic h2 h1
do
	python main.py $j 3g $ITERATIONS
done

Rscript plots.R 3g plt_box
Rscript plots.R 3g dom_box
Rscript plots.R 3g plt_cum
Rscript plots.R 3g dom_box
Rscript plots.R 3g plt_init
Rscript plots.R 3g plt_minusinit

