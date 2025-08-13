from pydantic_settings import BaseSettings
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()




class HikiVisionCongif(BaseModel):
    username: str
    password: str
    device_ip: str
    url: str


class RabbitMq(BaseModel):
    url: str
    queue_name: str



class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    camera: HikiVisionCongif
    rabbit: RabbitMq

    



settings = AppSettings()
