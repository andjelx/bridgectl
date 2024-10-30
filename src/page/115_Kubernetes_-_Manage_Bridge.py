import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.shared_bridge_settings import show_k8s_context
from src.page.ui_lib.stream_logger import StreamLogger
from src.bridge_logs import BridgeContainerLogsPath
from src.cli.bridge_status_logic import BridgeStatusLogic
from src.docker_client import DockerClient, ContainerLabels
from src.enums import RunContainerAsUser
from src.k8s_client import K8sClient, K8sPod
from src.models import AppSettings
from src.token_loader import TokenLoader


def btn_kill_bridge_pod(pod: K8sPod, app: AppSettings):
    st.write("")
    st.html(f"##### <span style='color:gray'>Deleting pod {pod.name}</span>")
    k8s_client = K8sClient()
    k8s_client.delete_pod(app.k8s_namespace, pod.name)
    st.text(f"k8s pod deleted")
    st.text(f"Calling Tableau Cloud API to remove agent")
    logger = StreamLogger(st.container())
    token = TokenLoader(logger).get_token_admin_pat()
    agent_name = pod.labels.get(ContainerLabels.tableau_bridge_agent_name)
    agent_sitename = pod.labels.get(ContainerLabels.tableau_sitename)
    BridgeStatusLogic(logger).remove_agent(token, agent_name, agent_sitename, logger)
    if st.button("Refresh 🔄"):
        st.rerun()

def btn_stout_logs(container_name: str, app: AppSettings):
    st.write("")
    st.html(f"#### <span style='color:gray'>{container_name} Logs</span>")
    logic = K8sClient()
    stdout_logs = logic.get_stdout_pod_logs(app.k8s_namespace, container_name)
    cont = st.container(height=500)
    cont.text(stdout_logs)

def btn_zip_logs(container_name):
    st.markdown(f"zipped Logs for **{container_name}**")

def btn_detail(container_name):
    st.write("")
    st.html(f"#### <span style='color:gray'>{container_name} Detail</span>")
    logic = K8sClient()
    app = AppSettings.load_static()
    detail = logic.get_pod_detail(app.k8s_namespace, DockerClient.bridge_prefix, container_name)
    if not detail:
        st.error(f"Pod {container_name} not found")
        return
    st.markdown(f"created: `{detail.created_ago}`")
    st.markdown(f"started: `{detail.started_ago}`")
    for k, v in detail.labels.items():
        st.markdown(f"{k}: `{v}`")
    rpm_source = detail.labels[ContainerLabels.tableau_bridge_rpm_source]
    user_as_tableau = (detail.labels[ContainerLabels.user_as_tableau] == RunContainerAsUser.tableau)
    st.markdown(f"bridge_logs_path: `{BridgeContainerLogsPath.get_logs_path(rpm_source, user_as_tableau)}`")
    st.markdown(f"image: `{detail.image_url}`")

def show_running_pods():
    cont1 = st.container()
    if not show_k8s_context(cont1):
        return
    if cont1.columns(2)[1].button("🔄"):
        st.rerun()
    cont1.markdown(f"#### Bridge Pods")
    k8s_client = K8sClient()
    status = k8s_client.check_connection()
    if not status.can_connect:
        st.error(f"Can't connect to kubernetes. {status.error}")
        return
    app = AppSettings.load_static()
    pods = k8s_client.get_pods_by_prefix(app.k8s_namespace, DockerClient.bridge_prefix)
    if not pods:
        st.markdown(f"No pods starting with `{DockerClient.bridge_prefix}` in k8s namespace: `{app.k8s_namespace}`")
        st.stop()

    col1, col2 = cont1.columns([3, 2])
    for idx, c in enumerate(pods):
        c: K8sPod = c
        cont = col1.container()
        cols = cont.columns([2, 1, 1, 1, 1, 1])
        cols[0].write(c.name)
        cols[1].text(c.phase)
        cols[2].text(c.started_ago)
        if cols[3].button(f"Detail", key=f"detail_{idx}"):
            btn_detail(c.name)
        if cols[4].button(f"💻 Logs", key=f"logs_{idx}"):
            btn_stout_logs(c.name, app)
        if cols[5].button(f"🗑️ Remove", key=f"rm_{idx}"): #FutureDev: try to use on_click() and see if the usability improves.
            btn_kill_bridge_pod(c, app)


def page_content():
    show_running_pods()
    st.markdown("")
    st.markdown("")


PageUtil.set_page_config("Manage K8s", "Manage Bridge Pods in Kubernetes", True)
page_content()
