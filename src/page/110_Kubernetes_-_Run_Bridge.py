import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.shared_bridge_settings import load_and_select_tokens, \
    show_k8s_context, view_mode_content, select_image_tags_from_ecr
from src.page.ui_lib.stream_logger import StreamLogger
from src import bridge_settings_file_util
from src.docker_client import DockerClient
from src.k8s_bridge_manager import K8sBridgeManager
from src.k8s_client import K8sSettings, K8sClient
from src.models import AppSettings


def page_content():
    st.info("Instructions to deploy bridge container images to kubernetes\n"
    "- Select a target kubernetes cluster on the [App Settings](/Settings?tab=k8s) page.\n"
    "- Select an bridge container image from the container registry. You can build an image and push to the container registry from the [Build Page](/Docker_-_Build)\n"
    "- Select a Personal Access Token (PAT) from the dropdown. Note that the name of the token will be used for the bridge agent name. [Add Tokens](/Settings)\n"
    "- Press the Deploy button.\n"
    "")
    st.markdown(f'#### Run Bridge Agent Settings')
    view_mode_content()

    # STEP - Show k8s context
    if not show_k8s_context(st.container()):
        return
    col1, col2 = st.columns([1, 2])
    col1.markdown(f"#### Run")
    app = AppSettings.load_static()
    image_tag, is_valid = select_image_tags_from_ecr(app, col1)
    if not image_tag:
        col1.warning("Container Image not selected, please configure a Container Registry on the [Settings](/Settings?tab=registry) page")
        return
    if not K8sSettings.does_kube_config_exist_with_warning(st):
        return
    # mgr = EcrRegistryPrivate(StreamLogger(st.container()), app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
    # img_detail = mgr.get_image_detail(image_tag) #FutureDev: get image detail including tags, so we can add those tags to the k8s pod.
    k8s_client = K8sClient()
    status = k8s_client.check_connection()
    if not status.can_connect:
        col1.warning(f"Can't connect to kubernetes. {status.error}")
        return
    pod_names = k8s_client.get_pod_names_by_prefix(app.k8s_namespace, DockerClient.bridge_prefix)
    pod_names2 = [p.replace("-","_",2) for p in pod_names]
    token_names, token_loader, tokens = load_and_select_tokens(col1, pod_names2, False)
    if col1.button("Deploy Bridge Container to Kubernetes"):
        create_bridge_pods(token_names, image_tag)
    # show_existing_pods(pod_names)

def create_bridge_pods(token_names, image_tag):
    req = bridge_settings_file_util.load_settings()
    app = AppSettings.load_static()
    mgr = K8sBridgeManager(StreamLogger(st.container()), req, app)

    for token_name in token_names:
        friendly_error = mgr.run_bridge_container_in_k8s(token_name, image_tag)
        if friendly_error:
            st.warning(friendly_error)
        else:
            st.success(f"Pod started")
    if st.button("Refresh 🔄"):
        st.rerun()

PageUtil.set_page_config("k8S Deploy Bridge", "Run Bridge Pods in Kubernetes", True)
page_content()
