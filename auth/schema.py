from pydantic import BaseModel, Field, field_validator

class UserRegistrationSchema(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    email: str = Field(min_length=10, max_length=60)
    password: str 

class UserLoginSchema(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    password: str

class UserProfileSchema(BaseModel):
    username: str
    email: str
    profile_picture: str
    
    model_config = {"from_attributes": True}