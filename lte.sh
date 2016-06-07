#!/bin/bash

mkdir lte
cp scripts/plots.R lte

for j in quic h2 h1
do
	python main.py $j lte 100
done

Rscript plots.R lte plt_box
Rscript plots.R lte dom_box
Rscript plots.R lte plt_cum
Rscript plots.R lte dom_box

