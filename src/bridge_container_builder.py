import os
from pathlib import Path

from src import download_util, bridge_settings_file_util
from src import models
from src.bridge_logs import BridgeContainerLogsPath
from src.bridge_rpm_download import BridgeRpmDownload
from src.docker_client import DockerClient, ContainerLabels
from src.driver_caddy.driver_script_generator import DriverScriptGenerator
from src.enums import BRIDGE_CONTAINER_PREFIX
from src.models import LoggerInterface, AppSettings, BridgeImageName, BridgeRpmSource

buildimg_path = f'{Path(__file__).parent.parent}{os.sep}buildimg'
driver_files_path = Path(buildimg_path) / "drivers"
bridge_client_config_filename = "TabBridgeClientConfiguration.txt"
bridge_client_config_path = Path(buildimg_path) / bridge_client_config_filename


class BridgeContainerBuilder:
    def __init__(self, logger: LoggerInterface, req: models.BridgeRequest):
        self.logger: LoggerInterface = logger
        self.req = req
        self.docker_client = DockerClient(self.logger)
        self.rpm_download = BridgeRpmDownload(logger, self.req.bridge.bridge_rpm_source, buildimg_path)
        self.driver_script_generator = DriverScriptGenerator(logger, buildimg_path)
        if not os.path.exists(buildimg_path):
            os.mkdir(buildimg_path)
        if not driver_files_path.exists():
            driver_files_path.mkdir()

    @staticmethod
    def set_runas_user(req, dockerfile_elements: dict):
        if req.bridge.user_as_tableau:
            dockerfile_elements["#<USER_CREATE>"] = """RUN groupadd --system --gid 1053 tableau && \\
        adduser --system --gid 1053 --uid 1053 --shell /bin/bash --home /home/tableau tableau && \\
        mkdir /bridge_setup && \\
        mkdir /home/tableau && \\
        chown -R tableau:tableau /home/tableau && \\
        chown -R tableau:tableau /bridge_setup\n"""
            dockerfile_elements["#<USER_SET>"] = """USER tableau\n"""
        else:
            dockerfile_elements["#<USER_SET>"] = "USER root"

    def build_bridge_image(self, re_download_rpm=False):
        self.logger.info("Build Tableau Bridge Docker Image")
        if not self.docker_client.is_docker_available():
            return
        if not os.path.exists(buildimg_path):
            os.mkdir(buildimg_path)
        req = self.req
        self.logger.info(f"working folder: {buildimg_path}")

        self.logger.info("STEP - Download Bridge RPM")
        if req.bridge.only_db_drivers:
            rpm_file = "n/a, drivers only"
        else:
            if re_download_rpm:
                self.logger.info(f"re-download bridge rpm: {re_download_rpm}")
            rpm_file = self.rpm_download.route_download_request_for_bridge_rpm(re_download_rpm)
            if rpm_file is None:
                self.logger.error(f"INVALID: Bridge rpm file not found in {buildimg_path}")
                return False
            if req.bridge.bridge_rpm_file != rpm_file:
                req.bridge.bridge_rpm_file = rpm_file
                bridge_settings_file_util.save_settings(req)

            self.logger.info(f"using local rpm file: {rpm_file}")
        if self.req.bridge.use_minerva():
            sub_run = {"TabBridgeClientWorker": "run-bridge.sh"}
        else:
            sub_run = None
        download_util.write_template(
            f"{Path(__file__).parent}/templates/start-bridgeclient.sh",
            f"{buildimg_path}{os.sep}start-bridgeclient.sh",
            True, replace=sub_run)

        if bridge_client_config_path.exists():
            self.logger.info(f"STEP - copy custom {bridge_client_config_filename} into image")
            home_path = "/home/tableau" if req.bridge.user_as_tableau else "/root"
            beta = "_Beta" if req.bridge.bridge_rpm_source == BridgeRpmSource.devbuilds else ""
            br_client_conf_copy = f"COPY {bridge_client_config_filename} {home_path}/tableau/Documents/My_Tableau_Bridge_Repository{beta}/Configuration/{bridge_client_config_filename}"
        else:
            br_client_conf_copy = "# SKIP"

        self.logger.info("STEP - Drivers")
        drivers_str = ",".join(req.bridge.include_drivers)
        self.logger.info(f"drivers to install: {drivers_str}")
        copy_driver_files = self.driver_script_generator.gen(req.bridge.include_drivers, req.bridge.linux_distro, True)
        copy_str = ""
        for d in copy_driver_files:
            copy_str += f"COPY ./drivers/{d} /tmp/driver_caddy/\n"
        copy_str = copy_str.rstrip()
        #STEP - Write Dockerfile
        dockerfile_elements = {
            "#<FROM_BASEIMAGE>": req.bridge.base_image,
            "#<USER_CREATE>": "",
            "#<USER_SET>": "",
            "#<COPY_DRIVER_FILES>": copy_str,
            "#<COPY_BridgeClientConfiguration>": br_client_conf_copy
        }
        
        self.set_runas_user(req, dockerfile_elements)

        docker_file = "Dockerfile_drivers_only" if req.bridge.only_db_drivers else "Dockerfile"
        download_util.write_template(
            f"{Path(__file__).parent}/templates/{docker_file}",
            f"{buildimg_path}/Dockerfile",
            replace=dockerfile_elements
        )

        labels = {
            ContainerLabels.database_drivers: drivers_str,
            ContainerLabels.tableau_bridge_rpm_version: rpm_file,
            ContainerLabels.tableau_bridge_rpm_source: req.bridge.bridge_rpm_source,
            ContainerLabels.base_image_url: req.bridge.base_image,
            ContainerLabels.tableau_bridge_logs_path: BridgeContainerLogsPath.get_logs_path(req.bridge.bridge_rpm_source, req.bridge.user_as_tableau)
        }

        self.logger.info("STEP - Build Docker image")
        docker_nocache = True
        build_args = {
            "BRIDGERPM": rpm_file
        }
        local_image_name = BridgeImageName.local_image_name(self.req)
        self.logger.info(f"image name: {local_image_name}")
        self.logger.info("this will take a few minutes ...")
        logs = self.docker_client.build_bridge_image(local_image_name, buildimg_path, build_args, labels, docker_nocache)
        # STEP - Set current selected image tag to this built image.
        if not req.bridge.only_db_drivers:
            app = AppSettings.load_static()
            l = local_image_name + ":latest"
            if app.selected_image_tag != l:
                app.selected_image_tag = l
                app.save()

        if logs:
            for line in logs:
                self.logger.info(line.get("stream"))
            return True
        else:
            return False

    @staticmethod
    def get_bridge_container_name(sitename, token_name) -> str:
        if not sitename:
            raise ValueError("site_name is empty")
        if not token_name:
            raise ValueError("token name is empty")
        return f"{BRIDGE_CONTAINER_PREFIX}{sitename}_{token_name}"


