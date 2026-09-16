from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    SYNC_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 500
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    UPLOAD_DIR:str ="uploads/profile_picture"   
    ALLOWED_PROFILE_PICTURE_TYPE:tuple = {"image/jpeg", "image/png"}
    MAX_PROFILE_PICTURE_FILE_SIZE: int = 5 * 1024 * 1024 
    
    ALLOWED_HOSTS: str    
    ALLOW_ORIGINS: str
    ALLOW_CREDENTIALS: bool
    ALLOW_METHODS: str
    ALLOW_HEADERS: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()