library("ggplot2")

plt_box <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_plt_boxplot.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = Site, y = PageLoadTime, fill=Protocol)) + geom_boxplot() + ggtitle("Page Load Time")
	ggsave(savefile)
}

dom_box <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_dom_boxplot.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = Site, y = DOMLoadTime, fill=Protocol)) + geom_boxplot() + ggtitle("DOM Load Time")
	ggsave(savefile)
}

plt_cum <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_plt_cumulativeplot.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = PageLoadTime, color=Protocol)) + stat_ecdf()  + ggtitle("Page Load Time")
	ggsave(savefile)
}

dom_cum <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_dom_cumulative_plot.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = DOMLoadTime, color=Protocol)) + stat_ecdf()  + ggtitle("DOM Load Time")
	ggsave(savefile)
}

plt_init <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_plt_init.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = Site, y = HandshakeTime, fill=Protocol)) + geom_boxplot() + ggtitle("Connection Establishment Time")
	ggsave(savefile)
}

plt_minusinit <- function(network_type) {
	loadfile <- paste(network_type, "/", "statistics.csv", sep="")
	savefile <- paste("plots", "/", network_type, "_plt_minusinit.pdf", sep="")
	data <- read.table(loadfile, sep=",", header=TRUE)

	ggplot(data, aes(x = Site, y = PageLoadTime - HandshakeTime, fill=Protocol)) + geom_boxplot() + ggtitle("Page Load Time - Connection Establishment Time")
	ggsave(savefile)
}

network_type = commandArgs()[6]
plot_type = commandArgs()[7]

main <- function(network_type, plot_type) {
	switch(
	plot_type,
	plt_box = plt_box(network_type),
	dom_box = dom_box(network_type),
	plt_cum = plt_cum(network_type),
	dom_cum = dom_cum(network_type),
	plt_init = plt_init(network_type),
	plt_minusinit = plt_minusinit(network_type),
	)
}

main(network_type, plot_type)



