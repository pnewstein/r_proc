readLines <- function(con, raw) {} # stop server from hanging
source("../r_subproc/server.R")

Sys.sleep(100)
send_string("test\n")
