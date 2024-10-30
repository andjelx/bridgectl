from time import sleep

import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.shared_bridge_settings import select_image_tags_from_ecr
from src.page.ui_lib.stream_logger import StreamLogger
from src.docker_client import DockerClient
from src.ecr_registry_private import EcrRegistryPrivate
from src.models import AppSettings, BridgeImageName


@st.dialog("Remove Image", width="large")
def remove_local_image(selected_local_image_tag, d_client: DockerClient):
    st.markdown(f"Remove local bridge image `{selected_local_image_tag}` ?")
    if st.button("Confirm Remove Image"):
        with st.spinner(""):
            ret = d_client.remove_image(selected_local_image_tag)
            if ret:
                st.success(f"removed local image {selected_local_image_tag}")
                sleep(3)
                st.rerun()

@st.dialog("Show Push Script", width="large")
def show_push_script(app, selected_local_image_name):
    cont = st.container(height=220, border=True)
    reg = EcrRegistryPrivate(StreamLogger(cont), app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
    _, cmds = reg.push_image(selected_local_image_name, None, True)
    c = "\n".join(cmds)
    cont.code(c, language='text')

def push_image_to_container_registry(cont, selected_local_image_name: str, app: AppSettings, d_client: DockerClient):
    if not selected_local_image_name:
        cont.info("Please select a local bridge image")
        return
    # img_detail = d_client.get_image_details(selected_local_image_name)
    if not app.is_ecr_configured():
        return
    cont1 = st.container()

    if cont.button("Push Image →"):
        reg = EcrRegistryPrivate(StreamLogger(st.container(height=320, border=True)), app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
        is_success, error = reg.check_connection_to_ecr()
        if not is_success:
            cont1.error(f"Unable to connect to ECR: {error}")
            return
        with st.spinner("pushing image ..."):
            reg.push_image(selected_local_image_name, d_client, False)
            cont1.success("pushed")
            return True
    else:
        if cont.button("Show Push Script"):
            show_push_script(app, selected_local_image_name)

def page_content():
    app = AppSettings.load_static()
    col1, col2 = st.columns(2)
    d_client = DockerClient(StreamLogger(st.container()))
    if not d_client.is_docker_available():
        return
    tags = d_client.get_tableeau_bridge_image_names()
    if not tags:
        col1.warning(f"No local docker images found with prefix {BridgeImageName.tableau_bridge_prefix}")
    tags.insert(0, "")
    col1.subheader("Local Bridge Images in Docker")
    selected_local_image_name = col1.selectbox(f" ", tags)
    did_push = push_image_to_container_registry(col1, selected_local_image_name, app, d_client)

    if selected_local_image_name and not did_push:
        if col1.button("Remove Local Image"):
            remove_local_image(selected_local_image_name, d_client)
    col2.subheader("Remote Bridge Images in AWS ECR")
    selected_image_tag, is_valid = select_image_tags_from_ecr(app, col2)
    if col2.button("← Pull Image"):
        with col2:
            with st.spinner(""):
                reg = EcrRegistryPrivate(StreamLogger(col2.container(height=420, border=True)), app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
                reg.pull_image(selected_image_tag)
                st.success("pulled")
    with col2.expander("..."):
        if st.button("refresh local ecr image cache"):
            app.ecr_image_tags_cache = None
            app.ecr_image_tags_cache_date = None
            app.save()
            st.rerun()


PageUtil.set_page_config("Publish Image to ECR", "Publish Image to Container Registry")
page_content()
