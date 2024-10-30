import inspect
import os
import pathlib
from dataclasses import dataclass
from abc import ABC, abstractmethod
import dataclasses
from datetime import datetime, timedelta
from typing import List, Dict

import yaml

from src.enums import DEFAULT_BASE_IMAGE, ADMIN_PAT_PREFIX, DEFAULT_LINUX_DISTRO, DEFAULT_BRIDGE_LOGS_PATH, \
    DEFAULT_DOCKER_NETWORK_MODE


@dataclass
class BaseClass:
    @classmethod
    def from_dict(cls, data: dict):
        ### Convert dictionary to Python class
        ### if a new property doesn't exist in an existing dictionary loaded from yaml then we should add that property with the default value specified in the class
        kwargs = {k: v for k, v in data.items() if k in inspect.signature(cls).parameters}
        return cls(**kwargs)

    def to_dict(self):
        return dataclasses.asdict(self)


class BridgeRpmSource:
    devbuilds = "devbuilds"
    tableau_com = "tableau.com"


@dataclass
class PatToken:
    name: str
    secret: str
    sitename: str
    pod_url: str = None
    site_id: str = None
    site_luid: str = None
    user_email: str = None
    pool_id: str = None
    pool_name: str = None

    def get_pod_url(self):
        return self.pod_url

    def is_admin_token(self):
        return self.name.startswith(ADMIN_PAT_PREFIX)

    def to_pat_token_secret(self):
        return PatTokenSecret(name=self.name, secret=self.secret)

@dataclass
class PatTokenSecret:
    name: str
    secret: str

    @staticmethod
    def from_dict(x: dict):
        return PatTokenSecret(name=x['name'], secret=x['secret'])

@dataclass
class TokenSite:
    """
    Stored in the bridge_tokens.yml
    """
    sitename: str
    pod_url: str
    site_luid: str = None
    site_id: str = None
    user_email: str = None
    dc_gw_token: str = None
    pool_id: str = None
    pool_name: str = None
    edge_manager_id: str = None
    gw_api_token: str = None #maybe rename to edge_api_token

    @staticmethod
    def from_dict(x: dict):
        return TokenSite(sitename=x.get('sitename'), pod_url=x.get('pod_url'), site_id=x.get('site_id'), site_luid=x.get('site_luid'),
                         user_email=x.get('user_email'), dc_gw_token=x.get('dc_gw_token'), pool_id=x.get('pool_id'), pool_name=x.get('pool_name'),
                         edge_manager_id=x.get('edge_manager_id'), gw_api_token=x.get('gw_api_token'))


@dataclass
class BridgeSiteTokens:
    site: TokenSite
    tokens: List[PatTokenSecret]

class TCUrls:
    PROD_USEAST = "https://prod-useast-a.online.tableau.com"
    ALPO_DEV = "https://us-west-2a.online.tableau.com"
    DEV_JUANITA = "https://dev-juanita.online.dev.tabint.net"
    all_urls = [PROD_USEAST, ALPO_DEV, DEV_JUANITA]

    def get_pod_name_from_url(self, url) -> str or None:
        for key, value in self.__class__.__dict__.items():
            if value == url:
                return key
        return None


@dataclass
class BridgeContainerSettings(BaseClass):
    include_drivers: List[str] = None
    base_image: str = None
    linux_distro: str = None
    bridge_rpm_source: str = BridgeRpmSource.tableau_com
    bridge_rpm_file: str = None
    use_minerva_rpm: bool = True
    user_as_tableau: bool = False
    image_name_suffix: str = None
    docker_network_mode: str = DEFAULT_DOCKER_NETWORK_MODE # valid values: 'bridge', 'host', (custom network name) #FutureDev: maybe move to AppSettings
    dns_mappings: Dict[str, str] = None
    unc_path_mappings: Dict[str, str] = None
    db_driver_eula_accepted: bool = False #FutureDev: move to AppSettings
    only_db_drivers: bool = False # only generate Dockerfile with drivers, no bridge rpm. image name prefix: "base_"

    def use_minerva(self):
        return self.bridge_rpm_source == BridgeRpmSource.devbuilds and self.use_minerva_rpm

@dataclass
class BridgeRequest(BaseClass):
    bridge: BridgeContainerSettings = None
    def __post_init__(self):
        if isinstance(self.bridge, dict):
            self.bridge = BridgeContainerSettings.from_dict(self.bridge)

def create_new_bridge_container_settings():
    return BridgeContainerSettings(
        base_image= DEFAULT_BASE_IMAGE,
        linux_distro= DEFAULT_LINUX_DISTRO,
        include_drivers= ["postgresql"])


app_settings_path = str(pathlib.Path(__file__).parent.parent / "config" / "app_settings.yml")
DEFAULT_VALID_LOGS_PATH_PREFIX = "~/Documents"

DEFAULT_ECR_REPOSITORY_NAME = "tableau-bridge"
# DEFAULT_ECR_PUBLIC_ALIAS = "l1p6i8f3"

class AppState:
    """
    AppState is a simple class that tracks if the app is loaded for the first time.
    """
    first_app_load: bool = True
    migrated_tokens: bool = False

APP_STATE = AppState()

@dataclass
class AppSettings:
    """
    AppSettings is a dataclass that holds all the application settings for the user (set at runtime by the user).
    """
    valid_log_paths_prefixes: List[str] = dataclasses.field(default_factory=list)
    logs_source_type: str = None
    logs_disk_path: str = DEFAULT_BRIDGE_LOGS_PATH
    logs_disk_file: str = None
    logs_docker_file: str = None
    logs_docker_container_name: str = None
    logs_k8s_pod_name: str = None
    logs_k8s_file: str = None
    devbuilds_username: str = ""
    devbuilds_password: str = ""
    streamlit_server_address: str = "localhost"
    feature_k8s_enabled: bool = False
    k8s_namespace: str = "tableau"
    feature_ecr_enabled: bool = False
    img_registry_type: str = None
    selected_image_tag: str = None
    aws_region: str = "us-west-2"
    ecr_private_aws_account_id: str = None
    ecr_private_repository_name: str = None
    ecr_image_tags_cache: List[str] = None
    ecr_image_tags_cache_date: datetime = None
    feature_show_dataconnect_publish: bool = False
    feature_additional_pages_enabled: bool = False
    feature_hammerhead_enabled: bool = False
    monitor_slack_api_key: str = None
    monitor_slack_recipient_email: str = None
    monitor_pager_duty_routing_key: str = None
    monitor_check_interval_hours: float = 1
    monitor_only_pools: List[str] = None
    monitor_enable_monitoring: bool = False
    autoscale_replica_count: int = 1
    autoscale_check_interval_hours: float = 1.0 #FutureDev: move to bridge/k8s settings
    autoscale_img_tag: str = None
    autoscale_show_page: bool = False
    feature_enable_edge_network_page: bool = False
    gw_api_token: str = None
    # edge_manager_id: str = None
    login_password_for_bridgectl: str = None

    def __post_init__(self):
        if not self.valid_log_paths_prefixes:
            self.valid_log_paths_prefixes.append(DEFAULT_VALID_LOGS_PATH_PREFIX)

    @staticmethod
    def load_static():
        app = AppSettings()
        app.load()
        return app

    def load(self, settings_file: str = app_settings_path):
        self._settings_file = settings_file
        if not os.path.exists(self._settings_file):
            return

        with open(self._settings_file, 'r') as infile:
            data = yaml.safe_load(infile)
        if not data:
            return

        props = set([f.name for f in dataclasses.fields(self)])
        # Drop unknown properties
        for k in set(data.keys()):
            if k not in props:
                data.pop(k)
        self.__init__(**data)

    def save(self):
        with open(self._settings_file, 'w') as outfile:
            yaml.dump(dataclasses.asdict(self), outfile, default_flow_style=False, sort_keys=False)
        # Store settings with tokens / passwords in secure way
        os.chmod(self._settings_file, 0o600)

    def is_ecr_configured(self):
        return self.feature_ecr_enabled and self.ecr_private_aws_account_id and self.ecr_private_repository_name

    def is_ecr_image_tags_cache_expired(self):
        ten_minutes = timedelta(minutes=10)
        return not self.ecr_image_tags_cache or datetime.now() - self.ecr_image_tags_cache_date > ten_minutes

    def set_ecr_image_tags_cache(self, tags: List[str]):
        self.ecr_image_tags_cache = tags
        self.ecr_image_tags_cache_date = datetime.now()


class LoggerInterface(ABC):
    @abstractmethod
    def info(self, msg: str = ""):
        pass

    @abstractmethod
    def warning(self, msg: str):
        pass

    @abstractmethod
    def error(self, msg: str, ex: Exception = None):
        pass


@dataclass
class LoginUser:
    username: str = None
    password_hash: str = None
    permissions: str = None


@dataclass
class LoginUserHash(LoginUser):
    password_hash: str = None


class ValidationException(Exception):
    pass

CONFIG_DIR = pathlib.Path(__file__).parent.parent / "config"


class BridgeImageName:
    tableau_bridge_prefix = "tableau_bridge"

    @staticmethod
    def version_from_file_name(rpm_file_name):
        version = rpm_file_name.replace(".x86_64.rpm", "") if rpm_file_name else ""
        return version.replace("tableau-bridge-", "").replace("TableauBridge-", "")

    @classmethod
    def local_image_name(cls, req: BridgeRequest):
        distro = req.bridge.linux_distro.lower() if req.bridge.linux_distro else "linux"
        if req.bridge.only_db_drivers:
            ver1 = ""
            prefix = "base"
        else:
            ver = cls.version_from_file_name(req.bridge.bridge_rpm_file)
            ver1 = "_" + ver if ver else ""
            prefix = cls.tableau_bridge_prefix
        suf = "_" + req.bridge.image_name_suffix if req.bridge.image_name_suffix else ""
        image_name = f"{prefix}_{distro}{ver1}{suf}"
        return image_name
