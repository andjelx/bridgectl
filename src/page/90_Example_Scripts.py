import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.stream_logger import StreamLogger
from src.bridge_container_builder import buildimg_path
from src.bridge_dockerfile_web_builder import BridgeDockerfileWebBuilder
from src.bridge_rpm_tableau_com import BridgeRpmTableauCom
from src import bridge_settings_file_util
from src.driver_caddy.driver_script_generator import DriverDefLoader
from src.enums import LINUX_DISTROS
from src.lib.usage_logger import USAGE_LOG, UsageMetric
from src.models import BridgeRpmSource


def page_content():
    PageUtil.horizontal_radio_style()
    st.info(f"""This page will help you create a Dockerfile and the scripts needed to build a Tableau Bridge container image.
Just select the options below.
Then copy the generated scripts below to a folder on a machine with Docker installed and run the docker build command to create a docker image or run a bridge container based on the image.
""")

    # STEP - query_parameters
    req = bridge_settings_file_util.load_settings()

    # STEP - Which Scripts
    w_bridge = "bridge scripts"
    w_just_drivers = "just drivers"
    opts = [w_bridge, w_just_drivers]
    which_scripts = st.radio("Which scripts", opts, 0)
    is_w_bridge = which_scripts == w_bridge

    st.markdown("#### Parameters")
    # STEP - Base Image
    base_image_examples = PageUtil.get_base_image_examples()
    req.bridge.base_image = st.text_input(f"Base image:", req.bridge.base_image,help = f"{base_image_examples}")
    # STEP - Linux Distro
    idx_d = 0 if req.bridge.linux_distro not in LINUX_DISTROS else LINUX_DISTROS.index(req.bridge.linux_distro)
    req.bridge.linux_distro = st.selectbox("Linux Distro", LINUX_DISTROS, idx_d)

    # STEP - Drivers
    driver_names = DriverDefLoader(StreamLogger(st.container())).get_driver_names(req.bridge.linux_distro)
    intersection_drivers = [x for x in req.bridge.include_drivers if x in driver_names]  # remove any invalid items stored in session state.
    if len(intersection_drivers) != len(req.bridge.include_drivers):
        missing_drivers = [driver for driver in req.bridge.include_drivers if driver not in driver_names]
        st.warning(f"Some previously selected database drivers are not available in driver definitions: {','.join(missing_drivers)}")
    req.bridge.include_drivers = st.multiselect("Edit Database Drivers", driver_names, default=intersection_drivers, help="Select which database drivers to install. Two scripts will be generated download_drivers.sh and install_drivers.sh")

    col1, col2 = st.columns(2)
    if is_w_bridge:
        # STEP - User Minerva
        if req.bridge.bridge_rpm_source == BridgeRpmSource.devbuilds:
            req.bridge.use_minerva_rpm = col1.checkbox("Use Minerva RPM (beta)", value=req.bridge.use_minerva_rpm, help="Check this box to use the new Minerva Bridge RPM, leave unchecked to use the stable DataServer Bridge RPM. Note the change to the download RPM url and start-bridgeclient.sh")
        # STEP - run as User
        req.bridge.user_as_tableau = col1.checkbox("container runas user: tableau", value=req.bridge.user_as_tableau, help="when unchecked, the container startup user is set to `root`, otherwise the container user is set to a lower privledge user named `tableau` (more secure)")

    # STEP - Latest Bridge RPM
    sl = StreamLogger(st.container())
    if is_w_bridge:
        if req.bridge.bridge_rpm_source == BridgeRpmSource.devbuilds:
            from src.internal.devbuilds.bridge_rpm_download_devbuilds import BridgeRpmDownloadDevbuilds
            rpm_file_d, rpm_url = BridgeRpmDownloadDevbuilds(sl, buildimg_path).just_get_name_and_url_of_latest()
            col1.markdown(f"Latest Bridge RPM from devbuilds: `{rpm_file_d}`")
        else:
            rpm_file = BridgeRpmTableauCom.get_file_name()
            col1.markdown(f"Latest Bridge RPM from tableau.com: `{rpm_file}`")

    col_s1, col_s2 = col1.columns(2)
    if col_s1.button("Show Scripts"):
        (dockerfile_contents, start_contents, build_sh_contents,
            download_contents, download_drivers_contents, install_drivers_contents, run_bridge_contents) = BridgeDockerfileWebBuilder(sl, req).generate_dockerfile()
        if is_w_bridge:
            st.markdown("#### Dockerfile")
            st.code(dockerfile_contents, language="text")
            st.markdown("#### start-bridgeclient.sh")
            st.code(start_contents, language="text")
            st.markdown("#### docker build command")
            st.code(build_sh_contents, language="text")
            st.markdown("#### bridge rpm download")
            st.code(download_contents, language="text")
        st.markdown("#### download_drivers.sh")
        st.code(download_drivers_contents, language="text")
        st.markdown("#### install_drivers.sh")
        st.code(install_drivers_contents, language="text")
        if is_w_bridge:
            st.markdown("#### run a bridge agent container")
            st.code(run_bridge_contents, language="text")
        USAGE_LOG.log_usage(UsageMetric.example_scripts_show)

    # STEP - Show Param Link
    st.markdown("")


PageUtil.set_page_config("Example Bridge Scripts", "Example Scripts for Tableau Bridge Containers and Drivers")
page_content()
