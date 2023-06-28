"""
Code that gives a python interface for a R process
"""

from typing import IO, Optional
from contextlib import AbstractContextManager
from subprocess import Popen, PIPE, TimeoutExpired, SubprocessError
from pathlib import Path
from enum import Enum
import threading
import sys

import numpy as np
from numpy.typing import NDArray

from .communicate import (
    VarType, GetValueRequest, GetValueResponse,
    ExecuteRequest, ExecuteResponse
)

SERVER_SCRIPT_PATH = Path(__file__).parent / "server.R"
TIMEOUT = .2

def string_to_np_array(in_bytes: bytes) -> NDArray[str]:
    """
    Converts a R string vector null terminated strings into a numpy array
    """
    out_array = np.array([s.decode("utf-8") for s in in_bytes.split(b"\x00")])
    # split adds the last null terminated string
    return out_array[1:-1]

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

    def eval_str(self, string: str, capture_output=False) -> tuple[str, str]:
        """
        Evalulates the string in R
        """
        if capture_output:
            raise NotImplementedError
        request = ExecuteRequest(size=len(string), capture_output=capture_output)
        self.stdin.write(request.json().encode("utf-8"))
        self.stdin.write(b"\n")
        self.stdin.flush()
        self.stdin.write(string.encode("utf-8"))
        self.stdin.flush()
        responce = self._readline_timeout()
        responce_obj: ExecuteResponse = ExecuteResponse.parse_raw(responce)
        if capture_output:
            std_out = self.stdout.read(responce_obj.std_out_len)
            std_err = self.stdout.read(responce_obj.std_out_len)
        return std_out, std_err

    def get_strings(self, var: str) -> NDArray[str]:
        """
        Gets the value attached to an R symbol
        """
        request = GetValueRequest(variable=var, var_type=VarType.str_vec)
        self.stdin.write(request.json().encode("utf-8"))
        self.stdin.write(b"\n")
        self.stdin.flush()
        responce = self._readline_timeout()
        responce_obj = GetValueResponse.parse_raw(responce)
        r_string = self.stdout.read(responce_obj.size)
        return string_to_np_array(r_string)

    # def clean_output(self):
        # """
        # Removes any lingering text in stdout
        # """
        # # closing statement causes R to print TOKEN
        # # the std.out is then read until the token to empty the pipe
        # self.stdin.write(CLOSING_STATEMENT)
        # self.stdin.flush()
        # read_until_token(self.stdout)

    # def eval_str(self, code: str) -> str:
        # """
        # Uses the R interperter to evaluate a string.
        # returns the interpreter's responce.
        # """
        # self.clean_output()
        # self.stdin.write(f"{code}\n".encode("utf-8"))
        # self.stdin.flush()
        # self.stdin.write(CLOSING_STATEMENT)
        # self.stdin.flush()
        # self.stdout.readline()
        # out = read_until_token(self.stdout)
        # return out.split(b"> write(\'~END~\', stdout())\n~END~\n>")[0].decode("utf-8")

    # def get_encoded(self, r_var: str) -> str:
        # """
        # Gets the content of an R variable
        # """
        # return self.eval_str(f"write({r_var}, stdout())")
