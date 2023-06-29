from subprocess import run, PIPE
from pathlib import Path
import json
import os

from r_subproc import communicate, r_proc
VarType = communicate.VarType

PROJECT_ROOT = Path(__file__).parents[1]

def test_json():
    gvr = communicate.GetValueRequest(**{"type": "GetValueRequest", "variable": "var", "var_type": communicate.VarType.double_vec})
    print(gvr.json())
    assert "\n" not in gvr.json()

def test_parse_response():
    responce = communicate.parse_response({"type": "GetValueResponse", "size": 5})
    assert (responce == communicate.GetValueResponse(type="GetValueResponse", size=5))

def test_r_write():
    """
    make sure there are no string terminator in writes
    """
    with r_proc.RProcess(PROJECT_ROOT / "test/r_write.R") as proc:
        responce = proc._readline_timeout(.2)
        out = proc.stdout.read(54)
        terminator = proc.stdout.read(1)
        assert (out[0] != b"\x00")




def test_communitcate_py_to_r():
    os.chdir(PROJECT_ROOT / "test")
    gvr = communicate.GetValueRequest(variable="a", var_type=VarType.double_vec, type="GetValueRequest")
    Path("get_value_request.json").write_text(gvr.json(), "utf-8")
    er = communicate.ExecuteRequest(body="Helllo", capture_output=False, type="ExecuteRequest")
    Path("execute_request.json").write_text(er.json(), "utf-8")

    r_code = b"""
source("../r_subproc/communicate.R")
test_requests()
    """
    out = run(["R", "--no-save"], cwd=(PROJECT_ROOT / "r_subproc"), check=True, input=r_code)

def test_communitcate_r_to_py():
    os.chdir(PROJECT_ROOT / "test")
    r_code = b"""
source("../r_subproc/communicate.R")
test_responses()
    """
    out = run(["R", "--no-save"], cwd=(PROJECT_ROOT / "r_subproc"), check=True, input=r_code)
    a = communicate.GetValueResponse.parse_raw(Path("get_value_response.json")
                                                 .read_bytes())
    b = communicate.ExecuteResponse.parse_raw(Path("execute_response.json")
                                                .read_bytes())

if __name__ == '__main__':
    test_r_write()
