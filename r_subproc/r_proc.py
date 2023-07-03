"""
Code that gives a python interface for a R process
"""

from typing import IO, Optional, Union, Type, Any

import json
from contextlib import AbstractContextManager
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError
from pathlib import Path
import threading

import numpy as np
from numpy.typing import NDArray
import pandas as pd
from scipy.sparse import csc_matrix

from .communicate import (
    VarType, GetValueRequest, GetValueResponse,
    ExecuteRequest, ExecuteResponse, ResponcesAlias, parse_response
)

SERVER_SCRIPT_PATH = Path(__file__).parent / "server.R"
TIMEOUT = 5

def string_to_np_array(in_bytes: bytes) -> NDArray[str]:
    """
    Converts a R string vector null terminated strings into a numpy array
    """
    out_array = np.array([s.decode("utf-8") for s in in_bytes.split(b"\x00")])
    return out_array

def double_to_np_array(in_bytes: bytes) -> NDArray[np.float64]:
    """
    Converts a R double vector into a numpy array
    """
    return np.frombuffer(in_bytes, np.float64)

def int_to_np_array(in_bytes: bytes) -> NDArray[np.int32]:
    """
    Converts a R double vector into a numpy array
    """
    return np.frombuffer(in_bytes, np.int32)

class RProcess(AbstractContextManager):
    """
    A session with the R interpreter
    """
    def __init__(self, file=None):
        """
        File is the R script to read
        """
        if file is None:
            file = SERVER_SCRIPT_PATH
        assert file.exists()
        self.proc = Popen(["Rscript", file], stdin=PIPE, stdout=PIPE,
                          stderr=PIPE, cwd=SERVER_SCRIPT_PATH.parent)
        if self.proc.stdout is None or self.proc.stdin is None:
            raise Exception()
        self.stdin: IO[bytes] = self.proc.stdin
        self.stdout: IO[bytes] = self.proc.stdout

    def __enter__(self) -> "RProcess":
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            outs, errs = self.proc.communicate(timeout=TIMEOUT)
        except TimeoutExpired:
            outs = None
            errs = b"Timeout Expired"
            self.proc.terminate()
        exit_code = self.proc.poll()
        if  exit_code != 0:
            if outs and errs:
                error_string = b"\n".join((errs, outs)).decode("utf-8")
            elif outs:
                error_string = outs.decode("utf=8")
            elif errs:
                error_string = errs.decode("utf=8")
            else:
                error_string = ""
            raise SubprocessError(
                f'R terminated {exit_code} with error: {error_string}'
            ) from exc_value

    def _readline_timeout(self, timeout: Optional[float] = None) -> bytes:
        """
        reads the stdout with a timeout
        """
        out_ba = bytearray()
        def read_into_stream(out_ba: bytearray):
            line = self.stdout.readline()
            # see if this is EOF
            if not line:
                if len(out_ba) != 0:
                    # the thread was killed 
                    print("dead thread")
                    return
                if self.proc.poll() is not None:
                    print("dead processes")
            out_ba.extend(line) #self.stdout.readline())
            # read the string terminator
            assert self.stdout.read(1) == b"\x00"

        if timeout is None:
            timeout = TIMEOUT
        read_thread = threading.Thread(target=read_into_stream, args=[out_ba])
        read_thread.start()
        read_thread.join(timeout=timeout)
        if read_thread.is_alive():
            # let the thread know
            out_ba.extend(b"killed")
            raise TimeoutExpired("readline", timeout)
        return bytes(out_ba)

    def _exchange_data(self, request: Union[GetValueRequest, ExecuteRequest]) -> ResponcesAlias:
        """
        Exchanges data with R
        """
        request_bytes = request.json().encode("utf-8")
        self.stdin.write(request_bytes)
        self.stdin.write(b"\n")
        self.stdin.flush()
        responce = self._readline_timeout()
        return parse_response(json.loads(responce.decode("utf-8")))


    def eval_str(self, string: str, capture_output=False) -> tuple[str, str]:
        """
        Evalulates the string in R
        """
        if capture_output:
            raise NotImplementedError
        request = ExecuteRequest(body=string, capture_output=capture_output)
        responce_obj: ExecuteResponse = self._exchange_data(request) # type: ignore
        if capture_output:
            std_out = self.stdout.read(responce_obj.std_out_len)
            std_err = self.stdout.read(responce_obj.std_out_len)
        else:
            std_out = std_err = b""
        return std_out.decode(), std_err.decode()

    def get_strings(self, var: str) -> NDArray[str]:
        """
        Gets the list of string attached to an R symbol
        """
        request = GetValueRequest(variable=var, var_type=VarType.str_vec)
        responce_obj: GetValueResponse = self._exchange_data(request) # type: ignore
        r_string = self.stdout.read(responce_obj.size).strip(b"\x00")
        return string_to_np_array(r_string)

    def get_doubles(self, var: str) -> NDArray[np.float64]:
        """
        gets the list of doubles attached to an R symbol
        """
        request = GetValueRequest(variable=var, var_type=VarType.double_vec)
        responce_obj: GetValueResponse = self._exchange_data(request) # type: ignore
        r_double = self.stdout.read(responce_obj.size)
        return double_to_np_array(r_double)

    def get_ints(self, var: str) -> NDArray[np.int32]:
        """
        gets the list of doubles attached to an R symbol
        """
        request = GetValueRequest(variable=var, var_type=VarType.int_vec)
        responce_obj: GetValueResponse = self._exchange_data(request) # type: ignore
        r_int = self.stdout.read(responce_obj.size)
        return int_to_np_array(r_int)

    def get_matrix(self, var: str, dtype: VarType, capture_output=False) -> pd.DataFrame:
        """
        Gets a sparce matrix from R
        """
        # drill vars
        r_string = f"drill_dgcmat({var})"
        self.eval_str(r_string)
        col_names: Optional[np.ndarray] = self.get_strings("col_names")
        assert col_names is not None
        if len(col_names) == 1:
            ncols  = int(col_names[0])
            col_names = None
        else:
            ncols = col_names.size
        row_names: Optional[np.ndarray] = self.get_strings("row_names")
        assert row_names is not None
        if len(row_names) == 1:
            nrows  = int(row_names[0])
            row_names = None
        else:
            nrows = row_names.size
        pointers = self.get_ints("p")
        index = self.get_ints("i")
        if dtype == dtype.int_vec:
            data: np.ndarray = self.get_ints("x")
        elif dtype == dtype.double_vec:
            data = self.get_doubles("x")
        elif dtype == dtype.str_vec:
            raise TypeError("You shouldn't have a sparse array of strings")
        else:
            assert False
        sparse_matrix = csc_matrix((data, index, pointers), (nrows, ncols))
        out = pd.DataFrame.sparse.from_spmatrix(sparse_matrix)
        if col_names is not None:
            out.columns = col_names
        if row_names is not None:
            out.index = row_names
        return out

    def get_df(self, var: str, capture_output=False) -> pd.DataFrame:
        """
        Gets a data_frame from R
        """
        rstring = f"drill_df({var})"
        self.eval_str(rstring)
        columns = self.get_strings("columns")
        types = self.get_strings("types")
        data_list: list[pd.Series] = []
        for i, (column_name, column_type) in enumerate(zip(columns, types)):
            if column_type == "character":
                data = self.get_strings(f"column{i}")
            elif column_type == "integer":
                data = self.get_ints(f"column{i}")
            elif column_type == "double":
                data = self.get_doubles(f"column{i}")
            else:
                assert False
            data_list.append(pd.Series(name=column_name, data=data))
        return pd.DataFrame(data_list).T
