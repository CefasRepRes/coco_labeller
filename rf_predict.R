## Example use:
# ./Rscript.exe ../../06-RF/rf_predict.R "../../../outputs/final_rf_model.rds" "../../../data/interim/features/stratified.csv" "../../../outputs/predictions.csv"
#If running in Rstudio: it is expected that you are running this at the command line. the wd is assumed to be setwd("C:/Users/JR13/Documents/LOCAL_NOT_ONEDRIVE/lucinda-flow-cytometry/scripts/R-4.3.3/bin/")
# command arguments are not named. Just uses index of arg[1] etc

library(randomForest)
model_in <- commandArgs(trailingOnly = TRUE)[1] # "../../../outputs/final_rf_model.rds" # ../../../outputs/peltic_trained_by_lucinda/variable_reduction/19_&__FINAL_PELTIC_TRAIN_strat.csv_final_rf_model.rds
filename_in <- commandArgs(trailingOnly = TRUE)[2] # "../../../data/features/stratified.csv"
filename_out <- commandArgs(trailingOnly = TRUE)[3] # "../../../outputs/predictions.csv"

stratified_data <- read.csv(filename_in)
model <- readRDS(model_in)

# Identify rows with any NAs in the expected terms
get_model_terms <- function(model) {
  terms_attr1 <- try(attr(terms(model), "term.labels"), silent = TRUE)
  terms_attr2 <- try(model[["finalModel"]][["xNames"]], silent = TRUE)  
  if (!inherits(terms_attr1, "try-error") && !is.null(terms_attr1)) {
    return(terms_attr1)
  } else if (!inherits(terms_attr2, "try-error") && !is.null(terms_attr2)) {
    return(terms_attr2)
  } else {
    stop("Model does not have a 'terms' attribute")
  }
}

expected_terms <- get_model_terms(model)

# Name mismatches... try fixing by substituting . for _
if(any(!expected_terms %in% names(stratified_data))){
  colnames(stratified_data) <- gsub("\\.", "_", colnames(stratified_data))}
print(expected_terms)
print(colnames(stratified_data))
if(any(!expected_terms %in% names(stratified_data))){stop("Variable names expected by model are not in your data")}
  
model_data <- stratified_data[, expected_terms]
valid_rows <- complete.cases(model_data)
na_indices <- which(!valid_rows)

#predict
predictions <- stats::predict(model, newdata = model_data[valid_rows, ])

# reinsert NAs
predictions_data <- rep("C_undetermined", nrow(model_data))
predictions_data[valid_rows] <- as.character(predictions)

combined_data <- cbind(stratified_data, predictions_data)
write.csv(combined_data, filename_out, row.names = FALSE)



# #loading packages
# library(tidyverse)
# library(caret)
# library(data.table)
# library(mclust)
# library(cvms)
# library(ggnewscale)
# library(rqdatatable)
# library(corrplot)
# input <- "E:/git_ex/lucinda-flow-cytometry/data/processed/validation"
# setwd(input)
# output_plot <- "E:/git_ex/lucinda-flow-cytometry/data/processed/plots/"
# output_metrics <- "E:/git_ex/lucinda-flow-cytometry/data/processed/metrics/"

# #total <- read.csv("peltic_500000_subsample.csv")
# #strat_train <- read.csv("peltic_strat_train.csv")
# #sub_train <- read.csv("peltic_subsample_train.csv")

# #test1 <- anti_join(total, strat_train)
# #test3 <- anti_join(test1, sub_train)
# #test.df <- select(test3, -starts_with("FWS_L_"), -starts_with("FWS_R_"))#"id" for peltic data
# #write.csv(test.df, "test_set.csv", row.names = FALSE)

# clean.valid.df <- function(valid.df, final.model){
  # label <- valid_df$label
  # valid.df2 <- select(valid_df, all_of(final.model[["finalModel"]][["xNames"]]))
  # valid.df2$label <- label
  # valid.df <- na.omit(valid.df2)
  # valid.df$label <- ifelse(valid.df$label == "OraMicro" | valid.df$label == "RedMicro", "Micro", valid.df$label)
  # valid.df$label<- as.factor(valid.df$label)
  # print(table(valid.df$label))
  # return(valid.df)
# }

# create.CM <- function(validation.data, prediction.vector, plot.name, metric.filename){
  # conf <- confusionMatrix(prediction.vector, validation.data$label)
  # Confusion.Matrix <- as.data.frame(conf$table)
  # stats.df <- as.data.frame(conf[["byClass"]])
  
  # confmat <- confusion_matrix(targets = validation.data$label, predictions = prediction.vector)
  # plot_confusion_matrix(conf_matrix = confmat$`Confusion Matrix`[[1]],
                        # add_normalized = FALSE,
                        # add_sums = TRUE,
                        # sums_settings = sum_tile_settings(
                          # label = "Total",
                          # palette = "Oranges",
                          # tc_tile_border_color = "black",
                          # tc_tile_border_size = 1,
                          # tile_border_color = "black",
                          # tile_border_size = 1
                        # ),
                        # rotate_y_text = FALSE,
                        # tile_border_color = "black",
                        # tile_border_size = 1,
                        # font_counts = font(size =4, hjust = 0.67, vjust = "left"),
                        # font_row_percentages = font(size = 3.5, vjust = 0.25),
                        # font_col_percentages = font(size = 3.5, vjust = 0.25))+
    # theme(text = element_text(size = 24, colour = "black"),
          # axis.text = element_text(colour = "black", size = 14),
          # axis.text.x = element_text(angle = 45, hjust = 0))
  # ggsave(filename = plot.name, path = output_plot, width = 10, height = 7)
  
  
  # cat("Exporting machine learning metrics ...", "\n")
  # write.csv(stats.df, metric.filename)
# }

# model_filename <- list.files("E:/git_ex/lucinda-flow-cytometry/models", pattern = "TRAIN_CHAFLR16")
# valid_filename <- list.files(pattern = "PAIR_TRAIN_CHAFLR16")
# prediction_list <- list()
# ref_list <- list()
# element_names <- c()
# element_names2 <- c()

# for (i in 1:length(model_filename)){
  # model_dir <- paste0("E:/git_ex/lucinda-flow-cytometry/models/", model_filename[[i]])
  # final.model <- get(load(model_dir))
  
  # for (j in 1:length(valid_filename)){
    # valid_df <- read.csv(valid_filename[[j]])
    
    # valid_df <- clean.valid.df(valid.df = valid_df, final.model = final.model)
    
    # if (i == 1){
      # ref_list[[length(ref_list) + 1]] <- valid_df$label
    # }
    
    # valid_variables <- select(valid_df, -label)
    # model_name <- sub(".RData", "", model_filename[[i]])
    # valid_name <- sub(".csv", "", valid_filename[[j]])
    # metric_name <- paste0(paste(valid_name, model_name, sep = "_"), "_metrics.csv")
    # metric_name <- paste0(output_metrics, metric_name)
    # plot_name <- paste0(paste(valid_name, model_name, sep = "_"), "_conf.png")
    
    # set.seed(42)
    # prediction <- predict(final.model, valid_variables)
    
    # create.CM(validation.data = valid_df, prediction.vector = prediction, plot.name = plot_name, metric.filename = metric_name)
    
    # prediction_list[[length(prediction_list) + 1]] <- prediction
    
    # if (i == 1){
      # element_names <- c(element_names, valid_name)
    # }
    
    # element_names2 <- c(element_names2, paste(model_name, valid_name, sep = "_&_"))
  # }
# }

# names(ref_list) <- element_names
# names(prediction_list) <- element_names2

# liste <- list("stratref-stratrf" = NULL,
              # "stratref-subrf" = NULL, 
              # "subref-stratrf" = NULL, 
              # "subref-subrf" = NULL)

# liste$`stratref-stratrf` <- adjustedRandIndex(ref_list[[1]], prediction_list[[1]])
# liste$`subref-stratrf` <- adjustedRandIndex(ref_list[[2]], prediction_list[[2]])
# liste$`stratref-subrf` <- adjustedRandIndex(ref_list[[1]], prediction_list[[3]])
# liste$`subref-subrf` <- adjustedRandIndex(ref_list[[2]], prediction_list[[4]])

# liste_df <- lapply(liste, as.data.frame)
# df <- as.data.frame(rbind(liste))
# df <- pivot_longer(df, c(1:length(liste_df)), names_to = "Pair", values_to = "ARI")
# df <- separate_wider_delim(df, Pair, "-", names = c("Col_1", "Col_2"))
# df2 <- pivot_wider(df, names_from = "Col_2", values_from = "ARI")
# df2 <- rename(df2, Col = Col_1)
# df3 <- pivot_wider(df, names_from = "Col_1", values_from = "ARI")
# df3 <- rename(df3, Col = Col_2)
# df2 <- data.frame(lapply(df2, function(x) {
  # gsub("NULL", NA, x)}))
# df3 <- data.frame(lapply(df3, function(x) {
  # gsub("NULL", NA, x)}))
# join <- natural_join(df2, df3, 
                     # by = "Col",
                     # jointype = "FULL")
# join <- relocate(join, stratrf, .after = Col)
# join <- relocate(join, stratref, .after = Col)
# join <- relocate(join, subref, .after = stratrf)
# join2 <- as.data.frame(lapply(join, str_replace_na))
# join2 <- as.data.frame(lapply(join2, function(x) {gsub("NA", 1, x)}))
# join2 <- as.data.frame(lapply(join2[,-1], as.numeric))
# final.df <- cbind(join[1],join2)
# final.array <- as.data.frame.array(final.df)
# rownames <- final.array$Col
# row.names(final.array) <- rownames
# final.array <- final.array[,-1]
# final.mat <- as.matrix(final.array)

# final.mat2 <- final.mat

# colnames(final.mat2) <- c("stratified reference", "stratified model", "random reference", "random model")
# rownames(final.mat2) <- c("stratified reference", "stratified model", "random reference", "random model")

# png("ari_chaflr16.png",
    # width=700, height=550)
# corrplot(corr = final.mat2, tl.col="black", na.label=" ", tl.cex = 2, cl.cex = 2, number.cex = 2, cl.align.text = "l", addCoef.col = "black", addgrid.col = "black",
         # type = "upper", diag = FALSE, method = "color", is.corr = FALSE, col.lim = c(0,1), col = COL1("Purples"))
# dev.off()