from pathlib import Path

from pytest import raises
import subprocess

from r_subproc import r_proc

HERE = Path(__file__).parent

# def test_string_to_array():
    # path = HERE / "string.bin"
    # with RSession() as r:
        # r.eval_str(f'writeBin(c("sdf", "dff", "lafsdfjslksldlsdv"), "{path}")')
    # string = (HERE / "string.bin").read_bytes()
    # assert np.all(r_proc.string_to_np_array(string) == ("sdf", "dff", "lafsdfjslksldlsdv"))

# def test_double_to_array():
    # path = HERE / "double.bin"
    # with RSession() as r:
        # r.eval_str(f'writeBin(c(1.01, 2.02, 3.03), "{path}")')
    # string = (HERE / "double.bin").read_bytes()
    # assert np.all(r_proc.double_to_np_array(string) == [1.01, 2.02, 3.03])

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
    r_proc.TIMEOUT = .1
    with r_proc.RProcess(HERE / "read_timeout_good.R") as proc:
        bytes = proc._readline_timeout(.2)
        # assert bytes == b'test\n'
        print(bytes)
    with raises(subprocess.SubprocessError):
        with r_proc.RProcess(HERE / "read_timeout_bad.R") as proc:
            bytes = proc._readline_timeout(.1)


if __name__ == '__main__':
    test_get_strings()
    test_init()
    test_get_strings_python()
    test_eval_str()
    test_readline_timeout()
