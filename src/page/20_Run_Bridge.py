from pathlib import Path

import streamlit as st

import src.token_loader
from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.pat_tokens_ui import add_pat_token_dialog, remove_pat_token_dialog
from src.page.ui_lib.shared_bridge_settings import select_image_tags_from_ecr, load_and_select_tokens, \
    view_mode_content
from src.page.ui_lib.stream_logger import StreamLogger
from src import bridge_settings_file_util
from src.bridge_container_runner import BridgeContainerRunner
from src.docker_client import DockerClient
from src.enums import ImageRegistryType, ADMIN_PAT_PREFIX
from src.lib.usage_logger import UsageMetric, USAGE_LOG
from src.models import AppSettings
from src.token_loader import TokenLoader


def start_run_bridge_container(token_names, cont_s, app: AppSettings):
    with st.spinner(""):
        for token_name in token_names:
            token = TokenLoader(StreamLogger(st.container())).get_token_by_name(token_name)
            if not token:
                cont_s.warning(f"INVALID: token_name {token_name} not found in {src.token_loader.token_file_path}")
                return
            req = bridge_settings_file_util.load_settings()
            runner = BridgeContainerRunner(StreamLogger(cont_s), req, token)
            is_success = runner.run_bridge_container_in_docker(app)
            if not is_success:
                return
            cont_s.success("Container Started")
        return True

def show_and_select_image_tags(cont, app: AppSettings):
    PageUtil.horizontal_radio_style()
    if not app.is_ecr_configured():
        img_reg_type = ImageRegistryType.local_docker
    else:
        options = [ImageRegistryType.local_docker, ImageRegistryType.aws_ecr]
        idx = options.index(app.img_registry_type) if app.img_registry_type in options else 0
        img_reg_type = cont.radio("Container Image Registry", options, index=idx)
    if img_reg_type != app.img_registry_type:
        app.img_registry_type = img_reg_type
        app.save()
    if app.img_registry_type == ImageRegistryType.aws_ecr:
        selected_image_tag, is_valid = select_image_tags_from_ecr(app, cont)
    else:
        selected_image_tag, is_valid = select_image_tags_local(app, cont)
    if app.selected_image_tag != selected_image_tag:
        app.selected_image_tag = selected_image_tag
        app.save()
    return is_valid

def select_image_tags_local(app: AppSettings, cont):
    tags = DockerClient(StreamLogger(st.container())).get_tableeau_bridge_image_names()
    idx = 0 if app.selected_image_tag not in tags else tags.index(app.selected_image_tag)
    selected_tag = cont.selectbox(f"Select Local Bridge Image ", tags, index=idx)
    if not tags:
        cont.warning("Please build bridge image")
        return None, False
    return selected_tag, True

def rerun_page():
    pass

def render_run_script(col1, app, selected_token_names):
    if app.streamlit_server_address and app.streamlit_server_address != "localhost":
        col1.warning("BridgeCTL Web UI server address is not 'localhost'. For security reasons the Show Run Script feature is only available on localhost")
        return
    if not app.selected_image_tag:
        col1.warning("Select an image tag")
        return
    req = bridge_settings_file_util.load_settings()
    cont=col1.container(height=900)
    p = Path(__file__).parent.parent / 'src' / 'templates' / 'run_bridge.sh'
    with open(p, 'r') as file:
        script_content = file.read()
    token_loader = TokenLoader(StreamLogger(cont))
    bst = token_loader.load()
    script_content += f"""
set -o errexit; set -o nounset; set -o xtrace

#STEP - Set variables
AWS_REGION="{app.aws_region}"
AWS_ACCOUNT_ID="{app.ecr_private_aws_account_id}"
AWS_ECR_IMAGE_REPO="{app.ecr_private_repository_name}"
BRIDGE_IMAGE_TAG="{app.selected_image_tag}"

TC_SERVER_URL="{bst.site.pod_url}"
SITE_NAME="{bst.site.sitename}"
USER_EMAIL="{bst.site.user_email}"
POOL_ID="{bst.site.pool_id}"

#STEP - Run bridge agents, one per PAT token
aws_login
"""
    if not selected_token_names:
        cont.warning("Select one or more PAT tokens to complete script")
        script_content += f"""
TOKEN_ID="<token name>"
set +o xtrace
TOKEN_VALUE="<token secret>"
set -o xtrace
run_container
"""
    for token_name in selected_token_names:
        token = token_loader.get_token_by_name(token_name)
        if not token:
            cont.warning(f"INVALID: token_name {token_name} not found in {src.token_loader.token_file_path}")
            return
        script_content += f"""
TOKEN_ID="{token.name}"
set +o xtrace
TOKEN_VALUE="{token.secret}"
set -o xtrace
run_container
"""
    cont.code(script_content, language='bash')

def run_bridge_container(existing_container_names):
    if not existing_container_names:
        existing_container_names = DockerClient(StreamLogger(st.container())).get_bridge_container_names()
    st.markdown("#### Run")
    PageUtil.horizontal_radio_style()
    col1, col2 = st.columns([2,1])
    app = AppSettings.load_static()
    is_valid = show_and_select_image_tags(col1, app)
    if app.img_registry_type == ImageRegistryType.aws_ecr:
        show_script = col1.checkbox("Show Run Script")
    else:
        show_script = False
    form = col1.form(key="st")
    selected_token_names, token_loader, tokens = load_and_select_tokens(form, existing_container_names)
    b_lbl = "Show Script for " if show_script else ""
    if form.form_submit_button(f"{b_lbl}Run Bridge Agent Containers", disabled=not is_valid):
        if not selected_token_names:
            form.warning("Please select one or more PAT tokens")
        else:
            if show_script:
                render_run_script(col1, app, selected_token_names)
            else:
                ret = start_run_bridge_container(selected_token_names, form, app)
                if ret:
                    st.button("Refresh 🔄", on_click=rerun_page)
                    USAGE_LOG.log_usage(UsageMetric.run_bridge_docker_container)
                else:
                    st.stop()
    col7, col8 = col1.columns([3,1])
    if col8.button("Add Token"):
        add_pat_token_dialog(None, token_loader)
    if col8.button("Remove Token"):
        remove_pat_token_dialog(None, token_loader)

def page_content():
    st.info("Instructions:\n"
        f'- Add Personal Access Tokens (PAT): Navigate to the [Settings](/Settings) page and add a PAT token per bridge agent and one token starting with "{ADMIN_PAT_PREFIX}".\n'
        '- Select a Target Pool: Use the "Edit" button to select a target pool for the bridge agents.\n'
        '- Build Image: Build a local bridge container image on the [build](/Docker_-_Build) page or select an image from ECR.\n'
        '- Select Tokens: From the dropdown menu, select one or more tokens. Each bridge agent must be associated with a unique PAT token. The name of the bridge agent will be the same as the name of the selected token.\n'
        '- Run the Container: Press Run Container to run a local bridge on linux container.\n')
    st.markdown(f'#### Run Bridge Agent Settings')
    view_mode_content()
    d_client = DockerClient(StreamLogger(st.container()))
    if not d_client.is_docker_available():
        return
    with st.spinner(""):
        existing_container_names = d_client.get_bridge_container_names()
        run_bridge_container(existing_container_names)


PageUtil.set_page_config("Run Bridge Containers", "Run Tableau Bridge Containers in Local Docker")
PageUtil.horizontal_radio_style()
page_content()
