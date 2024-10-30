import os
import pathlib
from dataclasses import dataclass, asdict

import yaml

from src.cli.app_logger import LOGGER

APP_NAME = "BridgeCTL"
APP_NAME_FOLDER = "bridgectl"

@dataclass
class AppConfig:
    """
    AppConfig holds all the application settings set at Deployment-time, (not set by the user).
    """
    config_filename: pathlib.Path
    app_version: str = "0.0.0"
    target_github_repo: str = None
    deployment_environment: str = None

    def __init__(self):
        self.config_filename = pathlib.Path(__file__).parent / "app_config.yaml"

        if not os.path.exists(self.config_filename):
            LOGGER.error(f'App config file not found at "{self.config_filename}"')
            exit(1)

    def load(self) -> 'AppConfig':
        with open(self.config_filename, 'r') as f:
            content = yaml.load(f, Loader=yaml.FullLoader)
        for k, v in content.items():
            self.__setattr__(k, v)
        return self

    def save(self):
        with open(self.config_filename, 'w') as outfile:
            save_data = asdict(self)
            save_data.pop('config_filename')
            yaml.dump(save_data, outfile, default_flow_style=False, sort_keys=False)

    def is_devbuilds(self):
        return self.target_github_repo.endswith(("tableautest.com"))

    @staticmethod
    def documentation_url():
        return "https://github.com/tableau/bridgectl"

APP_CONFIG: AppConfig = AppConfig().load()


class DeployEnviron:
    stable = "stable"
    beta = "beta"
    internal = "internal"
