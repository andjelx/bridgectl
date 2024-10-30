import json
import os
from pathlib import Path
from time import sleep

import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.stream_logger import StreamLogger
from src.bridge_container_builder import bridge_client_config_filename, \
    buildimg_path
from src.bridge_container_runner import BridgeContainerRunner
from src.docker_client import ContainerLabels
from src.docker_client import DockerClient
from src.lib.general_helper import StringUtils


@st.dialog("Remove Bridge Container", width="large")
def remove_container_dialog(bridge_container_name):
    st.markdown(f"Remove {bridge_container_name} ?")
    if st.button("Confirm Remove"):
        logger = StreamLogger(st.container())
        with st.spinner(""):
            BridgeContainerRunner.remove_bridge_container_in_docker(logger, bridge_container_name)
            sleep(1)
        st.rerun()

def btn_stout_logs(container_name):
    st.markdown(f"Logs for **{container_name}**")
    logic = DockerClient(StreamLogger(st.container()))
    stdout_logs = logic.get_stdout_logs(container_name)
    cont = st.container(height=500)
    cont.markdown(f"""```
{stdout_logs}
```""")

@st.dialog("Edit Bridge Client Configuration", width="large")
def edit_bridge_client_configuration(container_name):
    st.info("Fine tune the behavior of Tableau bridge by editing client configuration parameters " 
        f" stored in `{bridge_client_config_filename}`")
    st.markdown(f"target bridge container: `{container_name}`")
    col1,col2 = st.columns([3,1])
    col1.markdown("Current client configuration:")
    client = DockerClient(StreamLogger(st.container()))
    local_scratch_path = client.download_single_file_to_disk(container_name, bridge_client_config_filename, True)
    with open(local_scratch_path, "r") as f:
        content = f.read()
    is_edit = False #col2.checkbox("edit")
    if is_edit:
        edited = st.text_area("Client config", content, height=400)
    else:
        cont = st.container(height=400)
        cont.code(content, language="json")
    client_config  = json.loads(content)

    with st.form(key="edit_config"):
        current_connectionPool = client_config["serviceConnectionSettings"]["connectionPool"]["size"]
        selected_connectionPool = st.number_input("connectionPool", value= current_connectionPool, key = "connection_pool", min_value=1, max_value=100)
        current_maxRemoteJobConcurrency = client_config["dataSourceRefreshSettings"]["maxRemoteJobConcurrency"]
        selected_maxRemoteJobConcurrency = st.number_input("maxRemoteJobConcurrency", value =current_maxRemoteJobConcurrency, key="job_concurrency", min_value=1, max_value=100)
        current_jsonLogForExtractRefresh = client_config["dataSourceRefreshSettings"]["JSONLogForExtractRefresh"]
        idx = 1 if current_jsonLogForExtractRefresh == True else 0
        selected_jsonLogForExtractRefresh = (st.selectbox("JSONLogForExtractRefresh", ["false", "true"], idx, key="extract_logs") == "true")
        save_as_default = st.checkbox("save as default for new containers")
        if st.form_submit_button("Update Client Configuration"):
            no_op = (current_connectionPool == selected_connectionPool
                       and current_maxRemoteJobConcurrency == selected_maxRemoteJobConcurrency
                       and current_jsonLogForExtractRefresh == selected_jsonLogForExtractRefresh)
            if selected_connectionPool < selected_maxRemoteJobConcurrency:
                st.warning("connectionPool should be greater than or equal to maxRemoteJobConcurrency")
                return
            client_config["serviceConnectionSettings"]["connectionPool"]["size"] = selected_connectionPool
            client_config["dataSourceRefreshSettings"]["maxRemoteJobConcurrency"] = selected_maxRemoteJobConcurrency
            client_config["dataSourceRefreshSettings"]["JSONLogForExtractRefresh"] = selected_jsonLogForExtractRefresh
            if save_as_default:
                target = Path(buildimg_path) / bridge_client_config_filename
                with target.open("w") as f:
                    json.dump(client_config, f, indent=4)
                st.success("saved as default for future new containers")
            if no_op:
                st.warning("No changes detected")
                return
            is_success, out = client.edit_client_config_v2(container_name, client_config)
            st.text(out)
            if is_success:
                st.success(f"updated config for `{container_name}`")
                st.markdown("restarting container to apply changes")
                with st.spinner(""):
                    client.restart_container(container_name)
                    st.success("restart success")
            else:
                st.error(f"Error updating client configuration")

    if st.columns(2)[1].button("remove default"):
        target = Path(buildimg_path) / bridge_client_config_filename
        if target.exists():
            os.remove(target)
            st.success(f"removed default client configuration `{target}`")
        else:
            st.info(f"no default client configuration found at `{target}`")

def btn_zip_logs(container_name):
    st.markdown(f"zipped Logs for **{container_name}**")
    docker_client = DockerClient(StreamLogger(st.container()))
    zipf = docker_client.get_all_bridge_logs_as_tar(container_name)
    if not zipf:
        return
    with open(zipf, "rb") as f:
        st.download_button("Download Logs in TarGzip", f, file_name=f"bridge-logs-{container_name}.tgz")
    os.remove(zipf)

def btn_detail(container_name):
    st.write("")
    st.write("")
    st.write("")
    st.markdown(f"#### <span style='color:gray'>{container_name}</span>", unsafe_allow_html=True)
    logic = DockerClient(StreamLogger(st.container()))
    details = logic.get_container_details(container_name, True)
    col1, col2 = st.columns(2)
    col1.markdown(f"image name: `{details.image_name}`")
    col2.markdown(f"created: `{StringUtils.short_time_ago(details.image_create_date)}` ago")
    str_labels = ""
    for a in dir(ContainerLabels):
        if not a.startswith("__"):
            value = details.labels.get(a)
            str_labels += f"- {a}: `{value}`\n"
    st.markdown(f"container status: `{details.status}, started {details.started_ago} ago`")
    st.markdown("Labels: ")
    st.markdown(str_labels)
    c1,c2,c3 = st.columns(3)
    c1.metric("cpu", f"{details.cpu_usage_pct:.2f}%")
    c2.metric("mem", f"{details.mem_usage_mb:.2f}Mb")
    c3.metric("disk", details.disk_usage)
    st.markdown(f"JDBC Drivers: `{details.jdbc_drivers}`", help="list `.jar` files found in /opt/tableau/tableau_driver/jdbc")
    st.markdown(f"ODBC Drivers: `{details.odbc_drivers}`", help="ODBC entries returned by `odbcinst -q -d`")
    if details.network_mode:
        st.markdown(f"Network Mode: `{details.network_mode}`")
    if details.volume_mounts:
        st.markdown("Volume Mounts:")
        for vm in details.volume_mounts:
            st.markdown(f"  - `{vm}`")

def show_running_dockers():
    cont1 = st.container()
    cont1.markdown(f"### Local Bridge Containers")
    with st.spinner(""):
        doc = DockerClient(StreamLogger(st.container()))
        if not doc.is_docker_available():
            return
        containers = doc.get_containers_list(DockerClient.bridge_prefix)
        if not containers:
            st.write("No local bridge containers found, use the Run Bridge Container page to start one.")
            return

        col1, col2 = cont1.columns([3, 2])
        for idx, c in enumerate(containers):
            cont = col1.container()
            cols = cont.columns([2, 1, 1, 1, 2])
            cols[0].write(c.name)
            cols[1].text(c.status)
            if cols[2].button(f":material/info: Detail", key=f"detail_{idx}"):
                btn_detail(c.name)
            if cols[3].button(f":material/web_stories: Logs", key=f"logs_{idx}"):
                btn_stout_logs(c.name)
            with cols[4].expander("..."):
                if st.button(f":material/delete: Remove", key=f"rm_{idx}"): #FutureDev: try to use on_click() and see if the usability improves.
                    remove_container_dialog(c.name)
                if st.button(f":material/settings: Bridge client configuration", key=f"config_{idx}"):
                    edit_bridge_client_configuration(c.name)
                if st.button(f":material/folder_zip: zip all bridge logs", key=f"zip_{idx}"):
                    btn_zip_logs(c.name)

                # if st.button(f":material/terminal: nslookup", key=f"nslookup_{idx}"):
                #     st.write("nslookup")


def page_content():
    show_running_dockers()
    st.markdown("")
    st.markdown("")

PageUtil.set_page_config("Manage", "Manage Tableau Bridge Containers in Docker")
page_content()
