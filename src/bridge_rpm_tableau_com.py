import os

from src import download_util


class BridgeRpmTableauCom:
    # LATEST_RPM_URL = "https://downloads.tableau.com/tssoftware/TableauBridge-20242.24.0613.1930.x86_64.rpm"
    LATEST_RPM_URL = "https://downloads.tableau.com/tssoftware/TableauBridge-20242.24.0807.0327.x86_64.rpm"

    @classmethod
    def get_file_name(cls):
        return cls.LATEST_RPM_URL.split("/")[-1]

    @staticmethod
    def determine_and_download_latest_rpm_from_tableau_com(logger, buildimg_path, refresh_rpm: bool, just_get_name_of_latest: bool):
        rpm_file_name = BridgeRpmTableauCom.get_file_name()

        rpm_version = rpm_file_name.replace('.x86_64.rpm', '')
        if just_get_name_of_latest:
            return rpm_version
        asset_full_name = f"{buildimg_path}/{rpm_file_name}"
        if refresh_rpm and os.path.exists(asset_full_name):
            os.remove(asset_full_name)
        if os.path.exists(asset_full_name):
            logger.info(f"Latest Bridge RPM already downloaded: {asset_full_name}")
            return rpm_file_name
        logger.info(f"Downloading latest Bridge RPM: {BridgeRpmTableauCom.LATEST_RPM_URL}")
        download_util.download_file(BridgeRpmTableauCom.LATEST_RPM_URL, asset_full_name)
        return rpm_file_name