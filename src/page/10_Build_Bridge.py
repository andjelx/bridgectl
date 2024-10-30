import os
from time import sleep

import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.stream_logger import StreamLogger
from src.bridge_container_builder import BridgeContainerBuilder, buildimg_path, bridge_client_config_path
from src.bridge_rpm_download import BridgeRpmDownload
from src.bridge_rpm_tableau_com import BridgeRpmTableauCom
from src import bridge_settings_file_util
from src.cli.app_config import APP_CONFIG
from src.docker_client import DockerClient
from src.driver_caddy.driver_script_generator import DriverDefLoader
from src.driver_caddy.ui_driver_definition import UiDriverDefinition
from src.enums import LINUX_DISTROS, RunContainerAsUser, PropNames
from src.lib.usage_logger import USAGE_LOG, UsageMetric
from src.models import AppSettings, BridgeRpmSource, BridgeImageName, BridgeRequest
from src.validation_helper import Validation


def save_settings(db_drivers, bridge_rpm_source, use_minerva_rpm, base_image, user_as_tableau, linux_distro, image_name_suffix):
    req = bridge_settings_file_util.load_settings()
    req.bridge.include_drivers = db_drivers
    req.bridge.bridge_rpm_source = bridge_rpm_source
    req.bridge.base_image = base_image
    req.bridge.linux_distro = linux_distro
    req.bridge.user_as_tableau = user_as_tableau
    req.bridge.image_name_suffix = image_name_suffix
    if use_minerva_rpm is not None:
        req.bridge.use_minerva_rpm = use_minerva_rpm
    bridge_settings_file_util.save_settings(req)

@st.dialog("Accept Database Driver EULA", width="large")
def show_dialog_accept_db_eula(req):
    st.markdown("I acknowledge that the database driver install scripts provided here are examples only. "
                "I acknowledge that I have written my own database drive install scripts customized to my particular company "
                "needs and security policies. I acknowledge that I am in compliance with the database driver vendor terms of service. "
                "When required by the database driver vendor, I have accepted the database driver vendor's end user license agreement (EULA) on their respective "
                "websites and downloaded the driver from their website.")
    if st.button("Accept"):
        req.bridge.db_driver_eula_accepted = True
        bridge_settings_file_util.save_settings(req)
        st.success("Driver EULA Accepted")
        sleep(.7)
        st.rerun()

def page_content():
    PageUtil.horizontal_radio_style()
    st.info(f"""Select database drivers and enter a base image.
A local docker image will be created. Note that a Dockerfile and the required files will be copied to the folder `buildimg` which you can further customize if needed.
""")
    req = bridge_settings_file_util.load_settings()
    st.markdown("#### Build Parameters")
    colv_1, colv_2 = st.columns([2, 1])
    re_download_rpm = False
    colv_1.markdown(f"Base Image:`{req.bridge.base_image}` linux distro: `{req.bridge.linux_distro}`")
    # colv_1.markdown(f"Linux Distro: ```{req.bridge.linux_distro}```")
    drivers_list = ", ".join(req.bridge.include_drivers)
    colv_1.markdown(f"Database Drivers: ```{drivers_list}```")
    if colv_2.button("Edit ✎"):
        edit_build_parameters_dialog(req)
    with colv_2.expander("more parameters "):
        st.text("")
        st.text("")
        # c1, c2 = st.columns(2)
        if st.button("Import Driver Definition File"):
            UiDriverDefinition.define_drivers(req)
        if st.button("Upload Drivers"):
            UiDriverDefinition.upload_driver_setup_files()
        if APP_CONFIG.is_devbuilds():
            if st.button("Define UNC File Path Mappings"):
                edit_unc_path_mappings_dialog(req)
        # if st.button("Define DNS Mapping"):
        #     edit_dns_mapping(req)

    if req.bridge.only_db_drivers:
        colv_1.markdown("only build base image with drivers (skip bridge rpm): `true`")
    else:
        if req.bridge.bridge_rpm_source == BridgeRpmSource.devbuilds:
            download_from = " devbuildsweb.tsi.lan" if req.bridge.bridge_rpm_source == BridgeRpmSource.devbuilds else "downloads.tableau.com"
            rpm_downloaded = BridgeRpmDownload(colv_1, req.bridge.bridge_rpm_source, buildimg_path).get_rpm_filename_already_downloaded()
            r = rpm_downloaded if rpm_downloaded else "(latest rpm will be downloaded from devbuild/main)"
            colv_1.markdown(f"Bridge RPM: `{r}`  (from {download_from})")
            cols = colv_1.columns([1, 1])
            if rpm_downloaded:
                re_download_rpm = cols[0].checkbox("Download newer Bridge RPM")
            else:
                re_download_rpm = False
            cols[1].markdown(f"Use Minerva RPM: `{req.bridge.use_minerva()}`")
        else:
            colv_1.markdown(f"Bridge RPM: `{BridgeRpmTableauCom.get_file_name()}` (from tableau.com)")
    u = RunContainerAsUser.tableau if req.bridge.user_as_tableau else RunContainerAsUser.root
    colv_1a, colv_1b = colv_1.columns([1, 1])
    colv_1a.markdown(f"container runas user: `{u}`")
    if req.bridge.image_name_suffix:
        colv_1b.markdown(f"container image name suffix: `{req.bridge.image_name_suffix}`")
    if req.bridge.unc_path_mappings:
        colv_1b.markdown(f"UNC Path Mappings: `{len(req.bridge.unc_path_mappings)}`")
    if req.bridge.dns_mappings:
        colv_1b.markdown(f"DNS Mappings: `{len(req.bridge.dns_mappings)}`")
    if bridge_client_config_path.exists():
        colv_1.markdown(f"Use custom Bridge client configuration: `yes`", help= f"Client configuration file will be copied to the container image from this location {bridge_client_config_path}.")

    # if not APP_CONFIG.is_devbuilds():
    #     if not req.bridge.db_driver_eula_accepted:
    #         colv_2.warning("Please accept the database driver EULA before building the image.")
    #         if colv_2.button("Accept Driver EULA"):
    #             show_dialog_accept_db_eula(req)
    docker_client = DockerClient(StreamLogger(st.container()))
    if not docker_client.is_docker_available():
        st.stop()
    cont_feedback = st.container()
    if colv_1.button("Build Image"): #, disabled = not req.bridge.db_driver_eula_accepted):
        cont_success = cont_feedback.container()  # so that success message shows up before the long log.
        cont_log = cont_feedback.container(height=400)
        with st.spinner("building ..."):
            req = bridge_settings_file_util.load_settings()
            s_logger = StreamLogger(cont_log)
            status_ok = BridgeContainerBuilder(s_logger, req).build_bridge_image(re_download_rpm)
            if status_ok:
                cont_success.success("Image Built!")
                st.success("Image Build!")
                USAGE_LOG.log_usage(UsageMetric.build_bridge_image)
            else:
                cont_success.error("Image Build Failed")
    else:
        st.write("---")
    cb1, cb2 = st.columns([1,2])
    cb1.markdown("#### Built Image Details")
    img_detail = docker_client.get_image_details(BridgeImageName.local_image_name(req))
    if img_detail is None:
        cb1.write(f"No image labeled *{BridgeImageName.local_image_name(req)}*")
    else:
        cont = cb1.container(border=True)
        cont.markdown(f"Local Image Name: *{BridgeImageName.local_image_name(req)}*")
        cont.markdown(f"  Bridge RPM: *{img_detail.tableau_bridge_rpm_version}*")
        cont.markdown(f"  Bridge RPM Source: *{img_detail.tableau_bridge_rpm_source}*")
        cont.markdown(f"  Database Drivers: *{img_detail.database_drivers}*")
        # ad = f"*{img_detail.database_drivers_additional}*" if img_detail.database_drivers_additional else ""
        # cont.markdown(f"  Additional Database Drivers: {ad}")
        cont.markdown(f"  Image Size: *{img_detail.size_gb} GB*")
        cont.markdown(f"  Image Created Date: *{img_detail.created}*")

        # cb2.write(f"#### Publish Image to Container Registry")
        # push_image_to_container_registry(cb2, img_detail, req)


@st.dialog("Edit Build Parameters", width="large")
def edit_build_parameters_dialog(req):
    app_settings = AppSettings.load_static()
    base_image_examples = PageUtil.get_base_image_examples()
    base_image = st.text_input("Base Image (should be based on redhat 9)", req.bridge.base_image, help = f"{base_image_examples}")
    idx_d = 0 if req.bridge.linux_distro not in LINUX_DISTROS else LINUX_DISTROS.index(req.bridge.linux_distro)
    linux_distro = st.selectbox("Linux Distro", LINUX_DISTROS, idx_d)
    # linux_distro = LINUX_DISTROS[0]

    driver_names = DriverDefLoader(StreamLogger(st.container())).get_driver_names(linux_distro)
    intersection_drivers = [x for x in req.bridge.include_drivers if x in driver_names]  # remove any invalid items stored in session state.
    if len(intersection_drivers) != len(req.bridge.include_drivers):
        missing_drivers = [driver for driver in req.bridge.include_drivers if driver not in driver_names]
        st.warning(f"Some previously selected database drivers for linux_distro `{linux_distro}` are not available in driver definitions: `{','.join(missing_drivers)}`")
    selected_drivers = st.multiselect("Select Database Drivers", driver_names, default=intersection_drivers)

    col1, col2 = st.columns(2)
    if APP_CONFIG.is_devbuilds():
        rpm_sources = [BridgeRpmSource.tableau_com, BridgeRpmSource.devbuilds]
        idx = 0 if req.bridge.bridge_rpm_source not in rpm_sources else rpm_sources.index(req.bridge.bridge_rpm_source)
        bridge_rpm_source = col1.selectbox("Bridge RPM Download Source", rpm_sources, index=idx)
    else:
        bridge_rpm_source = BridgeRpmSource.tableau_com
        col1.markdown(f"Bridge RPM Download Source: `{bridge_rpm_source}`")
    if bridge_rpm_source == BridgeRpmSource.devbuilds:
        username = col1.text_input("devbuilds username", value=app_settings.devbuilds_username, label_visibility="collapsed")
        password = col1.text_input("devbuilds password", type="password", value=app_settings.devbuilds_password, label_visibility="collapsed")
        use_minerva_rpm = col1.checkbox("Use Minerva RPM", value=req.bridge.use_minerva_rpm)
    else:
        use_minerva_rpm = None
        col1.markdown(f"Latest Bridge RPM from tableau.com: `{BridgeRpmTableauCom.get_file_name()}`")
    user_as_tableau = col1.checkbox("container runas user: tableau", value=req.bridge.user_as_tableau, help="when unchecked, the container startup user is set to `root`, otherwise the container user is set to a lower privileged user named `tableau` (more secure)")
    image_name_suffix = col1.text_input("Docker Image Name Suffix (optional)", value=req.bridge.image_name_suffix, help="Optional suffix to append to the image name. You can use this field to help you remember which database drivers were selected or any other information specific to the image.")
    image_name_suffix = image_name_suffix if image_name_suffix is not None else ""
    if not Validation.is_valid_docker_image_name(image_name_suffix):
        col1.warning(f"Invalid image name suffix. must match pattern {Validation.valid_docker_image_pattern}")
        st.stop()
    if len(image_name_suffix) >= 50:
        col1.warning(f"Image name suffix must be less than 50 characters. Length is {len(image_name_suffix)}")
        st.stop()
    image_name_suffix = image_name_suffix.lower()

    col_s1, col_s2 = col1.columns(2)
    if col_s1.button("Save"):
        if bridge_rpm_source == BridgeRpmSource.devbuilds:
            app_settings.devbuilds_username = username
            app_settings.devbuilds_password = password
            app_settings.save()
        save_settings(selected_drivers, bridge_rpm_source, use_minerva_rpm, base_image, user_as_tableau, linux_distro, image_name_suffix)
        st.rerun()

def validate_paths(unc_network_share_path, host_mount_path, container_mount_path):
    errors = []
    if not unc_network_share_path:
        errors.append("UNC Network Share Path is required.")
    elif not unc_network_share_path.startswith("//"):
        errors.append(r"UNC Network Share Path must start with // (e.g., //server/share).")

    if not host_mount_path:
        errors.append("Host Mount Path is required.")
    elif not os.path.isabs(host_mount_path):
        errors.append("Host Mount Path must be an absolute path.")

    if not container_mount_path:
        errors.append("Container Mount Path is required.")
    elif not container_mount_path.startswith("/"):
        errors.append("Container Mount Path must start with / (e.g., /mnt/share).")
    elif not os.path.isabs(container_mount_path):
        errors.append("Container Mount Path must be an absolute path.")
    return errors

@st.dialog("Edit UNC Path Mappings", width="large")
def edit_unc_path_mappings_dialog(req: BridgeRequest):
    st.info("Define UNC Path Mappings for accessing network shares from the Bridge container. "
            "This allows Tableau Cloud to connect to file-based data sources stored on internal network shares. "
            "Note that the the Network share must be mounted on the host machine before starting the container. ")
    if req.bridge.unc_path_mappings is None:
        req.bridge.unc_path_mappings = {}
    if not req.bridge.unc_path_mappings:
        st.html(f"<span style='color:gray'>No mappings yet defined</span>")
    else:
        st.markdown("### Existing Mappings")
        paths: dict = {}
        for unc_path, paths in req.bridge.unc_path_mappings.items():
            host_mount_path = paths.get(PropNames.host_mount_path)
            container_mount_path = paths.get(PropNames.container_mount_path)
            st.markdown(f"- **UNC Path:** {unc_path}")
            st.markdown(f"  - **Host Mount Path:** {host_mount_path}")
            st.markdown(f"  - **Container Mount Path:** {container_mount_path}")
            st.markdown("---")
    st.markdown("### Add a mapping")
    unc_network_share_path = st.text_input(
        "UNC Network Share Path",
        key="unc_net",
        help=r"Enter the UNC path to the network share (e.g., \\\\server\\share)."
    )
    host_mount_path = st.text_input(
        "Host Mount Path",
        key="loc_mnt_path",
        help="Specify the path on the local host where the network share has been mounted."
    )
    if host_mount_path:
        if not os.path.exists(host_mount_path):
            st.warning("Host Mount Path does not exist on host")
        else:
            st.success("Host Mount Path exists on host")

    container_mount_path = st.text_input(
        "Container Mount Path",
        key="cont_mnt_path",
        help="Specify the path inside the container where the network share will be accessible."
    )

    if st.button("Add UNC Path Mapping"):
        unc_network_share_path = unc_network_share_path.strip()
        host_mount_path = host_mount_path.strip()
        container_mount_path = container_mount_path.strip()
        errors = validate_paths(unc_network_share_path, host_mount_path, container_mount_path)
        if errors:
            for e in errors:
                st.error(e)
                return
        else:
            req.bridge.unc_path_mappings[unc_network_share_path] = {PropNames.host_mount_path: host_mount_path, PropNames.container_mount_path: container_mount_path}
            bridge_settings_file_util.save_settings(req)
            st.success("UNC Mapping added")
            sleep(.7)
            st.rerun()
    st.info("Tips:\n"
            "- The mappings are used to mount network shares into the container at startup and tell Bridge how to find it. \n"
            "- UNC mappings stored in `bridgectl/config/bridge_settings.yml`. \n"
            "- To remove mappings, edit the YAML file directly. \n")

@st.dialog("Edit Local DNS Mappings", width="large")
def edit_dns_mapping(req: BridgeRequest):
    st.info("Define Local DNS Mappings to add to the /etc/hosts file inside the bridge container. \n"
            "These values will be passed into the --add_hosts parameter when running the bridge container.\n"
            "For example: `mydb.test.lan` and `10.22.33.44`")
    st.markdown("### Existing Mappings")
    if req.bridge.dns_mappings is None:
        req.bridge.dns_mappings = {}
    if not req.bridge.dns_mappings:
        st.warning("No DNS mappings yet defined")
    else:
        for host, ip in req.bridge.dns_mappings.items():
            col1, col2, col3 = st.columns([3, 3, 1])
            col1.markdown(f"**Host:** {host}")
            col2.markdown(f"**IP:** {ip}")
            if col3.button("Delete", key=f"delete_{host}"):
                del req.bridge.dns_mappings[host]
                bridge_settings_file_util.save_settings(req)
                st.success(f"Deleted mapping for host: {host}")
                sleep(.7)
                st.rerun()

    st.markdown("### Add a mapping")
    host = st.text_input("Host", key="host")
    ip = st.text_input("IP Address", key="ip")
    if st.button("Add DNS Mapping"):
        host = host.strip()
        ip = ip.strip()
        if not host or not ip:
            st.error("Host and IP are required")
            return
        if not Validation.is_valid_host(host):
            st.error(f"Invalid Host: {host}")
            return
        if not Validation.is_valid_ipaddress(ip):
            st.error(f"Invalid IP Address: {ip}")
            return
        req.bridge.dns_mappings[host] = ip
        bridge_settings_file_util.save_settings(req)
        st.success("DNS Mapping added")
        sleep(.7)
        st.rerun()


PageUtil.set_page_config("Build", "Build Tableau Bridge Container Image")
page_content()
