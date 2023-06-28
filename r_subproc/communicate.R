source("utils.R")

library(jsonlite)

# returns json then a then_do
GetValueRequest <- function(variable, var_type) {
    value <- get(variable, envir = python_env)
    if (var_type == "str_vec") {
        size <- string_vector_bytes(value)
        then_do <- list("send_string", value)
    } else if (var_type == "double_vec") {
        size <- double_vector_bytes(value)
        then_do <- list("send_vector_bytes", value)
    }
    return(list(construct_get_value_response(size), then_do))
}

# returns json then a then_do
ExecuteRequest <- function(size, capture_output) {

    code <- readLines(con = file("/dev/stdin", raw = TRUE), size)
    #code <- readChar(con = "stdin", size)
    is.null(code)
    log(nchar(code))

    if (capture_output) {
        texts <- eval_capture_output()
        # TODO get the sizes of stdout
    } else {
        eval_no_capture(code)
        json_out <- construct_execute_response(0, 0)
        log(json_out)
        then_do <- list("nothing")
    }
    return(list(json_out, then_do))
}

construct_get_value_response <- function(size) {
    return(toJSON(list(type = "GetValueResponse", size = size),
                  auto_unbox = TRUE))
}

construct_execute_response <- function(std_out_len, std_err_len) {
    return(toJSON(list(type = "ExecuteResponse", std_out_len = std_out_len,
                       std_err_len = std_err_len), auto_unbox = TRUE))
}

# Uses R magic to call the first item in the list
# with the rest as args
dispatch_request <- function(json) {
    request <- fromJSON(json)
    return(do.call(request$type, args = request[-1], envir = python_env))
}


test_requests <- function() {
    dispatch_request(readLines("get_value_request.json"))
    dispatch_request(readLines("execute_request.json"))
}

test_responses <- function() {
    writeLines(construct_get_value_response(5), "get_value_response.json")
    writeLines(construct_execute_response(20, 30), "execute_response.json")
}
