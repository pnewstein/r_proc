from pathlib import Path
import subprocess

from pytest import raises
import numpy as np

from r_subproc import r_proc
from r_subproc.communicate import VarType

HERE = Path(__file__).parent


def test_double_to_array():
    string = b'\x9a\x99\x99\x99\x99\x99\xf1?\x9a\x99\x99\x99\x99\x99\x01@'
    out = r_proc.double_to_np_array(string)
    assert np.all(r_proc.double_to_np_array(string) == [1.1, 2.2])


def test_init():
    with r_proc.RProcess() as proc:
        print(proc)

def test_get_strings():
    with r_proc.RProcess(HERE / "test_strings.R") as proc:
        out = proc.get_strings("a")
        assert(len(out) == 2)

def test_get_strings_python():
    with r_proc.RProcess() as proc:
        out = proc.get_strings("test_string")
        print(out)
        assert(len(out) == 2)
        out = proc.get_strings("test_string")
        out = proc.get_strings("test_string")
        print(out)
        assert(len(out) == 2)

def test_eval_str():
    with r_proc.RProcess() as proc:
        proc.eval_str("a<-'2'")
        out = proc.get_strings("a")
        assert out[:] == "2"

def test_readline_timeout():
    with r_proc.RProcess(HERE / "read_timeout_good.R") as proc:
        bytes = proc._readline_timeout()
        # assert bytes == b'test\n'
        print(bytes)
    with raises(subprocess.SubprocessError):
        with r_proc.RProcess(HERE / "read_timeout_bad.R") as proc:
            bytes = proc._readline_timeout(.1)


def test_get_doubles():
    with r_proc.RProcess() as proc:
        proc.eval_str("a <- c(1.1, 2.2, 3.03)")
        out = proc.get_doubles("a")
        assert np.all(out == np.array([1.1, 2.2, 3.03]))

def test_get_ints():
    with r_proc.RProcess() as proc:
        proc.eval_str("a <- c(as.integer(1), as.integer(999))")
        out = proc.get_ints("a")
        assert np.all(out == np.array([1, 999]))

make_matrix = """
library(Matrix)
test_mat <- Matrix(c(0, 0,  0, 2,
                     6, 0, -1, 5,
                     0, 4,  3, 0,
                     0, 0,  5, 0),
                   byrow = TRUE, nrow = 4, sparse = TRUE)
"""
def test_mat():
    with r_proc.RProcess() as proc:
        proc.eval_str(make_matrix)
        matrix = proc.get_matrix("test_mat", VarType.double_vec)
        print(matrix)


if __name__ == '__main__':
    # test_get_strings()
    # test_init()
    # test_get_strings_python()
    # test_eval_str()
    # test_double_to_array()
    # test_get_strings()
    # test_get_ints()
    test_mat()
