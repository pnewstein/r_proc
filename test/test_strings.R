source("../r_subproc/communicate.R")
source("../r_subproc/utils.R")

a <- c("Hello Python!", "how are you?")
out <- construct_get_value_response(string_vector_bytes(a))
cat(out)
cat("\n")
writeBin(a, "/dev/stdout")
