from pydantic import BaseModel, Field, field_validator
from auth.schema import UserProfileSchema

class ItemReadSchema(BaseModel):
    id: int
    name: str
    user_id: int
    user: UserProfileSchema
    
    model_config = {"from_attributes": True}

class ItemCreateSchema(BaseModel):
    name: str