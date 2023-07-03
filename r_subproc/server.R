source("communicate.R")
source("compound_types.R")


log <- function(str = "", clear = FALSE) {
    if (clear) {
        write("", file = "R.log")
    }
    write(str, file = "R.log", append = TRUE)
}

stdout <- file("/dev/stdout", open = "wb", raw = TRUE)

send_string <- function(string) {
    log(string)
    writeBin(con = stdout, object = string)
    flush(stdout)
}

send_vector_bytes <- function(string) {
    send_string(string)
}

nothing <- function() {
}

python_env <- new.env()
assign("test_string", c("This is from R", "read it from python"),
       envir = python_env)


serve <- function() {
    # clear log
    log(clear = TRUE)

    while (TRUE) {
    input <- readLines(con = file("/dev/stdin", raw = TRUE), 1)
    log(input)
    if (length(input) == 0) {
        # received EOF
        log("received EOF")
        return()
    }
    log(get("test_string", envir = python_env))
    out <- dispatch_request(input)
    log(out[[1]])
    send_string(sprintf("%s\n", out[[1]]))
    then_do <- out[[2]]
    log(paste(then_do[[1]]))
    do.call(then_do[[1]], args = then_do[-1], envir = python_env)
    }
}

test_get_value_str <- function() {
    # echo "source(\"server.R\");test_get_value()" | R --no-save
    assign("a", c("new phone, who dis", "its me!"), envir = python_env)
    out <- dispatch_request('{"type": "GetValueRequest", "variable": "a", "var_type": "str_vec"}')
    print(out)
}

test_eval_str <- function() {
    # echo "a<-10" | Rscript server.R
    out <- dispatch_request('{"type": "ExecuteRequest", "size": 5, "capture_output": false}')
    print(out)
    get("a", envir = python_env)
}
serve()
