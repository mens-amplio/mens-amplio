# Makes some plots, prints them to PDF.
# Assumes filenames are of the following form: [wet/dry]-[condition].csv
# e.g. wet-meditation.csv
# ...or use "-k.csv" suffix if applicable

require("ggplot2")

base_dir = "~/code/mens_amplio/python-mindwave-mobile/"
setwd(paste(base_dir, "measurements/sarah-5min", sep=""))
outfile <- paste(base_dir, "analysis/sarah-5min-plots.pdf", sep="")
file_list <- list.files(pattern = "\\.csv$")


for (file in file_list){
  temp_dataset <-read.table(file, header=TRUE, sep=",")
  
  # set condition info and elapsed time
  temp_dataset$gel <- substr(file,1,3)
  temp_dataset$condition <- substr(file,5,nchar(file)-4)
  temp_dataset$k <- ifelse(grepl('-k',file), "y", "n")
  temp_dataset$time_elapsed <- temp_dataset$timestamp - min(temp_dataset$timestamp)
       
  # if the merged dataset doesn't exist, create it
  if (!exists("raw_data")){
    raw_data <- temp_dataset
  }
   
  # if the merged dataset does exist, append to it
  if (exists("raw_data")){
    raw_data<-rbind(raw_data, temp_dataset)
  }
  
  rm(temp_dataset)
}

# exclude bad datapoints
data <- subset(raw_data,poor_signal == 0 & (attention>0 | meditation>0) )

# break up into subsets by condition
wet_all <- data[data$gel == "wet",]
wet <- wet_all[wet_all$k == "n",]
dry <- data[data$gel == "dry",]
k <- data[data$k == "y",]

# Allocate list to hold plots (have to change size manually for now)
p <- vector(mode="list", length=10) 

# histograms by condition
p[[1]] <- ggplot(wet,aes(x=meditation, fill=condition)) + geom_density(alpha=0.3) #means not different, less variability in 2back condition
p[[2]] <- ggplot(wet,aes(x=attention, fill=condition)) + geom_density(alpha=0.3) #mean is higher in meditation condition (ha)
p[[3]] <- ggplot(dry,aes(x=attention, fill=condition)) + geom_density(alpha=0.3) #only meaningful difference here is "don't eat"
p[[4]] <- ggplot(dry,aes(x=meditation, fill=condition)) + geom_density(alpha=0.3) #same
p[[5]] <- ggplot(k, aes(x=meditation, fill=condition)) + geom_density(alpha=0.3)
p[[6]] <- ggplot(k, aes(x=attention, fill=condition)) + geom_density(alpha=0.3)

# modest negative correlations between meditation and attention w/wet, uncorrelated w/dry
p[[7]] <- ggplot(wet, aes(x=attention, y=meditation, color=condition)) + geom_point(alpha=.3) + geom_smooth(width=1.5, method=lm)
p[[8]] <- ggplot(wet, aes(x=attention, y=meditation, color=condition)) + geom_point(alpha=.3) + geom_smooth(width=1.5, method=lm)

# timecourses
p[[9]] <- ggplot(wet, aes(time_elapsed, meditation, color=condition)) + geom_point(alpha=.3) + geom_smooth(aes(group=condition), method=loess, width=1.5)
p[[10]] <- ggplot(wet, aes(time_elapsed, attention, color=condition)) + geom_point(alpha=.3) + geom_smooth(aes(group=condition), method=loess, width=1.5)

library(gridExtra)

# print to PDF
pdf(outfile, onefile = TRUE)
for (i in seq(length(p))) {
  print( p[[i]] )
}
dev.off()
