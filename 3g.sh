#!/bin/bash

mkdir 3g
cp scripts/plots.R 3g

for j in quic h2 h1
do
	python main.py $j 3g 100
done

Rscript plots.R 3g plt_box
Rscript plots.R 3g dom_box
Rscript plots.R 3g plt_cum
Rscript plots.R 3g dom_box

