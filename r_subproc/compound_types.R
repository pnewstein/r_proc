# drills the dgtmat into vectors saved in python_env

library(Matrix)

drill_dgcmat <- function(dgcmat) {
  row_names <- dgcmat@Dimnames[[1]]
  if (length(row_names) == 0) {
    row_names <- as.character(dgcmat@Dim[1])
  }
  assign("row_names", row_names, envir = python_env)
  col_names <- dgcmat@Dimnames[[2]]
  if (length(col_names) == 0) {
    col_names <- as.character(dgcmat@Dim[2])
  }
  assign("col_names", col_names, envir = python_env)
  assign("i", dgcmat@i, envir = python_env)
  assign("p", dgcmat@p, envir = python_env)
  assign("x", dgcmat@x, envir = python_env)
}


test_dig_out_type <- function(symbol) {
  var <- get(symbol, envir = python_env)
  stopifnot(typeof(var) %in% c("double", "integer", "character"))
}

test_fun <- function() {
    test_mat <- Matrix(c(0, 0,  0, 2,
                         6, 0, -1, 5,
                         0, 4,  3, 0,
                         0, 0,  5, 0),
                       byrow = TRUE, nrow = 4, sparse = TRUE)

    python_env <- new.env()
    drill_dgcmat(test_mat)
    test_dig_out_type("p")
    test_dig_out_type("i")
    test_dig_out_type("x")
    test_dig_out_type("col_names")
    test_dig_out_type("row_names")
}
#a <- readRDS("dgc.rds")
