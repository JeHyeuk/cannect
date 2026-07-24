from functools import lru_cache
from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    CODEBEAMER_ID:str
    CODEBEAMER_PW:str
    COMPANY_NAME: str ="HYUNDAI KEFICO Co., Ltd."
    COMPANY_NAME_KOR: str
    DIVISION_NAME: str
    DIVISION_NAME_KOR: str
    ETAS_PATH: Path
    SERVER_IP: str
    SERVER_PORT: str
    SERVER_TEMP: Path
    SVN_PATH: Path

    model_config = SettingsConfigDict(
        env_file=Path(__file__).absolute().parent / '.env',
        extra='allow'
    )

    @computed_field
    @property
    def ASCET_PATH(self) -> Path:
        return self.ETAS_PATH / "ASCET6.1"

    @computed_field
    @property
    def COPYRIGHT(self) -> str:
        return f'ⓒCopyright {self.COMPANY_NAME} All rights reserved.'

    @computed_field
    @property
    def DOWNLOADS(self) -> Path:
        return Path.home() / "Downloads"

    @computed_field
    @property
    def CB_AUTH(self) -> Path:
        return Path(__file__).absolute().parent / '.cb-auth.json'

    @computed_field
    @property
    def BASELINE_PATH(self) -> Path:
        return Path(r'\\kefico\keti\ENT_Engine_mgt\01_EMS_SW')

    def __getitem__(self, item):
        return self.__getattribute__(item)

    def __setitem__(self, key, value):
        self.__setattr__(key, value)


@lru_cache()
def get_settings() -> Settings:
    return Settings(**os.environ)

# Alias
env = settings = get_settings()

if __name__ == "__main__":
    # print(env)
    # print(env.model_dump_json(indent=4))
    env['new_env'] = 'abc'
    print(env.SERVER_TEMP)
    print(env['new_env'])