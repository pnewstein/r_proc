from typing import (
    Union, Literal, Annotated, TYPE_CHECKING,
    TypeVar, Type
)
from enum import Enum, auto
from abc import ABC, abstractclassmethod


from pydantic import BaseModel, Field
from dataclasses import dataclass

if TYPE_CHECKING:
    class BaseModel(ABC): # pylint: disable=no-redef
        @abstractclassmethod
        def parse_raw(cls: Type[T], json: bytes) -> T:
            pass
        def json(self) -> str:
            pass


class VarType(Enum):
    """
    The type of R variable
    """
    double_vec = "double_vec"
    str_vec = "str_vec"
    int_vec = "int_vec"

class ExecuteRequest(BaseModel):
    """
    The next text will be R code to execute
    """
    type: Literal["ExecuteRequest"] = "ExecuteRequest"
    body: str
    "the size of the string"
    capture_output: bool
    "whether to capture stdout and stderr"

class ExecuteResponse(BaseModel):
    """
    The response to code execution
    the next text will be stdout and stderr
    """
    type: Literal["ExecuteResponse"] = "ExecuteResponse"
    std_out_len: int
    std_err_len: int

class GetValueRequest(BaseModel):
    """
    A request for the value of a variable
    """
    type: Literal["GetValueRequest"] = "GetValueRequest"
    variable: str
    "the symbol to get the value of"
    var_type: VarType
    "the type of variable"

class GetValueResponse(BaseModel):
    """
    the response to the get_value request
    the next line will contain the data
    """
    type: Literal["GetValueResponse"] = "GetValueResponse"
    size: int

ResponcesAlias = Union[GetValueResponse, ExecuteResponse]

def parse_response(response_dict: dict) -> ResponcesAlias:
    ResponseValue = Annotated[ResponcesAlias, Field(discriminator="type")]
    class Response(BaseModel):
        response: ResponseValue
    return Response(response=response_dict).response
