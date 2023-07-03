readLines <- function(con, raw) {}
source("../r_subproc/server.R")


send_string(sprintf("%s\n", '{"type":"GetValueResponse","size":3}'))
log("written")

out_string <- "23903824903248902348902348908908908sdfjsddsafjklsdaf"

size <- string_vector_bytes(out_string)

log(size)
send_string(out_string)

