from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class ClassroomResponse(BaseModel):
    id: int
    class_code: str
    class_name: str
    max_students: int
    status: str

    model_config = ConfigDict(
        from_attributes=True
    )


class StudentCreate(BaseModel):
    student_code: str = Field(
        ...,
        min_length=3,
        max_length=20
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )
    email: EmailStr
    age: int = Field(
        ...,
        ge=16,
        le=60
    )
    gender: Literal[
        "male",
        "female",
        "other"
    ]
    class_id: int = Field(
        ...,
        ge=1
    )


class StudentUpdate(BaseModel):
    student_code: Optional[str] = Field(
        None,
        min_length=3,
        max_length=20
    )
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100
    )
    email: Optional[EmailStr] = None
    age: Optional[int] = Field(
        None,
        ge=16,
        le=60
    )
    gender: Optional[
        Literal[
            "male",
            "female",
            "other"
        ]
    ] = None
    class_id: Optional[int] = Field(
        None,
        ge=1
    )


class StudentResponse(BaseModel):
    id: int
    student_code: str
    full_name: str
    email: EmailStr
    age: int
    gender: str
    class_id: int
    classroom: ClassroomResponse

    model_config = ConfigDict(
        from_attributes=True
    )


class APIResponse(BaseModel):
    statusCode: int
    message: str
    data: object | None
    error: object | None
    timestamp: str
    path: str