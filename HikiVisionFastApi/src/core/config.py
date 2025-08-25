from pydantic_settings import BaseSettings
from pydantic import BaseModel, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv 


load_dotenv()



class ApiV1Routes(BaseModel):
    prefix: str = "/v1"
    users: str = "/users"


class ApiRoutes(BaseModel):
    prefix: str = "/api"
    v1: ApiV1Routes = ApiV1Routes()


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    

class HikiVisionCongif(BaseModel):
    username: str
    password: str
    

class HttpBase(BaseModel):
    base_url: str
    
    
    
class JwtConfig(BaseModel):
    access_secret_key: str        
    refresh_secret_key: str
    algorithm: str
    access_token_minutes: int
    refresh_token_days: int  
    
    


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10


    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )

    server: ServerConfig = ServerConfig()
    api: ApiRoutes = ApiRoutes()
    db: DatabaseConfig
    camera: HikiVisionCongif
    jwt: JwtConfig
    http: HttpBase

    



settings = AppSettings()

