library("ggplot2")

bp <- function() {
	data <- read.table("statistics.csv", sep=",", header=TRUE)
	
	ggplot(data, aes(x = Site, y = PageLoadTime, fill=Protocol)) + geom_boxplot() + ggtitle("Boxplot") + coord_fixed(ratio=0.2)
	ggsave("plot.pdf")	
}

bp()
