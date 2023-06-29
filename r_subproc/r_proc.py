"""
Code that gives a python interface for a R process
"""

from typing import IO, Optional, Union, Type

import json
from contextlib import AbstractContextManager
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError
from pathlib import Path
import threading

import numpy as np
from numpy.typing import NDArray

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
            # read the string terminator
            assert self.stdout.read(1) == b"\x00"
            out_ba.extend(line) #self.stdout.readline())

        if timeout is None:
            timeout = TIMEOUT
        read_thread = threading.Thread(target=read_into_stream, args=[out_ba])
        read_thread.start()
        read_thread.join(timeout=timeout)
        if read_thread.is_alive():
            # let the thread know
            out_ba.extend(b"killed")
            raise TimeoutExpired("readline", timeout)
        return bytes(out_ba).strip(b"\x00")

    def _exchange_data(self, request: Union[GetValueRequest, ExecuteRequest]) -> ResponcesAlias:
        """
        Exchanges data with R
        """
        self.stdin.write(request.json().encode("utf-8"))
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
        Gets the value attached to an R symbol
        """
        request = GetValueRequest(variable=var, var_type=VarType.str_vec)
        responce_obj: GetValueResponse = self._exchange_data(request) # type: ignore
        r_string = self.stdout.read(responce_obj.size).strip(b"\x00")
        return string_to_np_array(r_string)
