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
    } else if (var_type == "int_vec") {
        size <- int_vec_bytes(value)
        then_do <- list("send_vector_bytes", value)
    }
    return(list(construct_get_value_response(size), then_do))
}

# returns json then a then_do
ExecuteRequest <- function(body, capture_output) {
    if (capture_output) {
        texts <- eval_capture_output(body)
        # TODO get the sizes of stdout
    } else {
        eval_no_capture(body)
        json_out <- construct_execute_response(0, 0)
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
    python_env <<- new.env()
    assign("a", "what", envir = python_env)
    assign("Helllo", "what", envir = python_env)
    dispatch_request(readLines("../test/get_value_request.json"))
    dispatch_request(readLines("../test/execute_request.json"))
}

test_responses <- function() {
    writeLines(construct_get_value_response(3), "../test/get_value_response.json")
    writeLines(construct_execute_response(20, 30), "../test/execute_response.json")
}
