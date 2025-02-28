from pydantic.types import StringConstraints
from pydantic import BaseModel
from typing_extensions import Annotated
from fastapi import Path

class UserAuthorization(BaseModel):
    username: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_ ]+$", min_length=3, max_length=20)]
    password: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9@#%^&+=]+$", min_length=8, max_length=64)]

class UsersName(BaseModel):
    first_name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_ ]+$", min_length=3, max_length=20)]
    last_name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_ ]+$", min_length=3, max_length=20)]
    
class FaceIdRegex(BaseModel):
    face_id: Annotated[int, Path(..., title="Face ID", description="ID must be a positive integer", ge=1)]

class UserIdRegex(BaseModel):
    user_id: Annotated[int, Path(..., title="User ID", description="ID must be a positive integer", ge=1)]