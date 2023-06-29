readLines <- function(con, raw) {} # stop server from hanging
source("../r_subproc/server.R")

a <- c("Hello Python!", "how are you?")
out <- construct_get_value_response(string_vector_bytes(a))
send_string(sprintf("%s\n", out))
writeBin(a, "/dev/stdout")
