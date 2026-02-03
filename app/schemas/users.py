from pydantic import BaseModel

class ChangePasswordReq(BaseModel):
    old_password: str
    new_password: str

class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"
    
class UpdateUserRequest(BaseModel):
    name: str | None = None
    surname: str | None = None

class UpdateUserResponse(BaseModel):
    message: str = "User updated successfully"
    
class DeleteUserResponse(BaseModel):
    message: str = "User deleted successfully"