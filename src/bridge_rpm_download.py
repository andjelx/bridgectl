import os

from src import models
from src.bridge_rpm_tableau_com import BridgeRpmTableauCom
from src.lib.general_helper import StringUtils
from src.models import LoggerInterface


class BridgeRpmDownload:
    def __init__(self, logger: LoggerInterface, bridge_rpm_source: str, buildimg_path: str):
        self.logger = logger
        self.bridge_rpm_source = bridge_rpm_source
        self.buildimg_path = buildimg_path

    def just_get_name_and_url_of_latest(self):
        if self.bridge_rpm_source == models.BridgeRpmSource.devbuilds:
            from src.internal.devbuilds.bridge_rpm_download_devbuilds import BridgeRpmDownloadDevbuilds
            rpm_filename, url = BridgeRpmDownloadDevbuilds(self.logger, self.buildimg_path).just_get_name_and_url_of_latest()
            return rpm_filename, url
        else:
            rpm_file_name = BridgeRpmTableauCom.get_file_name()
            url = BridgeRpmTableauCom.LATEST_RPM_URL
            return rpm_file_name, url

    def get_rpm_filename_already_downloaded(self) -> str:
        if self.bridge_rpm_source == models.BridgeRpmSource.devbuilds:
            prefix = "tableau-bridge"
        else:
            prefix = "TableauBridge"
        if os.path.exists(self.buildimg_path):
            files = [f for f in os.listdir(self.buildimg_path) if f.startswith(prefix) and f.endswith(".rpm")]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.buildimg_path, x)), reverse=True) #sort by newest file first
            if files:
                return files[0]
            else:
                return None
        return ""

    def route_download_request_for_bridge_rpm(self, refresh_rpm: bool) -> str:
        if self.bridge_rpm_source == models.BridgeRpmSource.devbuilds:
            rpm_downloaded = self.get_rpm_filename_already_downloaded()
            if rpm_downloaded and not refresh_rpm:
                rpm_file = rpm_downloaded
            else:
                if refresh_rpm:
                    local_file_name = f"{self.buildimg_path}/{rpm_downloaded}"
                    os.remove(local_file_name)
                from src.internal.devbuilds.bridge_rpm_download_devbuilds import BridgeRpmDownloadDevbuilds
                rpm_file = BridgeRpmDownloadDevbuilds(self.logger, self.buildimg_path).determine_and_download_latest_rpm_fromdevbuilds()
        elif self.bridge_rpm_source == models.BridgeRpmSource.tableau_com:
            rpm_file = BridgeRpmTableauCom.determine_and_download_latest_rpm_from_tableau_com(self.logger, self.buildimg_path, refresh_rpm, False)
        else:
            raise Exception(f"bridge_rpm_source {self.bridge_rpm_source} not supported. valid values: {StringUtils.get_values_from_class(models.BridgeRpmSource)}'")
        return rpm_file
