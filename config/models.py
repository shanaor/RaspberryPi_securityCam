import re
from pydantic.types import StringConstraints
from pydantic import BaseModel, field_validator
from typing_extensions import Annotated
from typing import Optional, List

class UserAuthorization(BaseModel):
    username: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9_ ]+$", min_length=3, max_length=20)]
    password: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z0-9@#%^&+=]+$", min_length=8, max_length=64)]

    @field_validator("password")
    def validate_password_complexity(cls, password):
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[@#%^&+=]", password):
            raise ValueError("Password must contain at least one special character (@#%^&+=)")
        return password

class FaceName(BaseModel):
    first_name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z ]+$", min_length=3, max_length=20)]
    last_name: Annotated[str, StringConstraints(pattern=r"^[a-zA-Z ]+$", min_length=3, max_length=20)]
    encoding: Optional[List[float]] = None
    