from time import sleep
from typing import List

import streamlit as st

from src.page.ui_lib.stream_logger import StreamLogger
from src.bridge_container_builder import BridgeContainerBuilder
from src.cli.bridge_status_logic import get_or_fetch_site_id
from src.ecr_registry_private import EcrRegistryPrivate
from src.enums import DEFAULT_POOL
from src.k8s_client import K8sSettings
from src.lib.tc_api_client import TableauCloudLogin, TCApiLogic, BridgePool
from src.models import AppSettings
from src.token_loader import TokenLoader


def bridge_settings_view():
    cont = st.container()
    bst = TokenLoader(StreamLogger(cont)).load()
    col1, col2 = cont.columns([1, 2])
    col1.markdown(f"Pool: **`{bst.site.pool_name}`**")
    col2.markdown(f"Sitename: **`{bst.site.sitename}`**")
    return col1

def view_mode_content():
    col1 = bridge_settings_view()
    col1, col2 = col1.columns(2)
    if col1.button("Edit"):
        edit_mode_dialog()

@st.dialog("Select Bridge Pool", width="large")
def edit_mode_dialog():
    token_loader = TokenLoader(StreamLogger(st.container()))
    # req = bridge_settings_file_util.load_settings()
    admin_pat = token_loader.get_token_admin_pat()
    if not admin_pat:
        st.html(f"You can add PAT tokens on the <a href='/Settings'>Settings</a> page")
    else:
        with st.spinner("Fetching bridge pool information from Tableau API"):
            login_result = TableauCloudLogin.login(admin_pat, True)
            logic = TCApiLogic(login_result)
            # site_info = logic.api.get_session_info()  # FutureDev cache in bridge_settings
            site_id = get_or_fetch_site_id(logic.api, admin_pat, StreamLogger(st.container()))
            pool_list = logic.get_pool_list(site_id)
            pool_list.insert(0, BridgePool(DEFAULT_POOL, DEFAULT_POOL))
            user_email = admin_pat.user_email

            with st.form(key="edit_bridge_pool"):
                col1, col2 = st.columns(2)
                idx = next((i for i, member in enumerate(pool_list) if member.id == admin_pat.pool_id), 0)
                selected_pool = col1.selectbox("Bridge Pool", pool_list, format_func= lambda x: x.name, placeholder="Select a pool", index= idx)
                col2.text(f"Tableau Cloud Sitename: {admin_pat.sitename}")
                col2.text(f"Url: {admin_pat.pod_url}")
                col2.text(f"User email: {user_email}") # FutureDev: add a way to change user email
                col2.text(f"Pool Name: {admin_pat.pool_name}")
                col2.text(f"Pool ID: {admin_pat.pool_id}")

                if st.form_submit_button("Confirm and Save"):
                    if not selected_pool:
                        col1.warning("Pool is required")
                    else:
                        token_loader.update_pool_id(selected_pool.id, selected_pool.name)
                        # pool_id = selected_pool.id
                        # req.bridge.pool_name = selected_pool.name
                        # req.bridge.user_email = user_email
                        # req.bridge.pod_url = admin_pat.pod_url
                        # req.bridge.site_name = admin_pat.sitename.lower()
                        # bridge_settings_file_util.save_settings(req)
                        st.success("Saved")
                        sleep(.7)
                        st.rerun()

def select_image_tags_from_ecr(app: AppSettings, cont, show_error: bool = False):
    if not app.is_ecr_configured():
        cont.warning("AWS ECR Container Registry not configured. Please edit in [Settings](/Settings?tab=registry)")
        return None, False
    else:
        mgr = EcrRegistryPrivate(StreamLogger(cont), app.ecr_private_aws_account_id, app.ecr_private_repository_name, app.aws_region)
        url = mgr.get_repo_url()
        if app.is_ecr_image_tags_cache_expired():
            tags, error = mgr.list_ecr_repository_tags()
            if error:
                if show_error:
                    cont.warning("Error fetching tags from ECR")
                return None, False
            app.set_ecr_image_tags_cache(tags)
            app.save()
        idx = 0 if app.selected_image_tag not in app.ecr_image_tags_cache else app.ecr_image_tags_cache.index(app.selected_image_tag)
        return cont.selectbox(f"Select Image from `{url}`", app.ecr_image_tags_cache, index=idx), True

def load_and_select_tokens(cont, existing_container_names, is_docker: bool = True) -> (List[str], TokenLoader, List):
    token_loader = TokenLoader(StreamLogger(cont))
    tokens = token_loader.load_tokens()
    selected_tokens = None
    if tokens is None:
        tokens = []
    token_names = []
    in_use_token_names = []
    for t in tokens:
        if t.is_admin_token():
            continue
        if BridgeContainerBuilder.get_bridge_container_name(t.sitename, t.name) in existing_container_names:
           in_use_token_names.append(t.name)
        else:
            token_names.append(t.name)
    if len(token_names) > 0:
        token_names.insert(0, "")
        col1, col2 = cont.columns([2, 1])
        selected_tokens = col1.multiselect("Select PAT Tokens", token_names)
    else:
        cont.warning("Please add PAT tokens. One PAT Token is required per bridge agent.")
    runtime = "local docker" if is_docker else "kubernetes"
    cont.columns([1,2])[1].html(f"<span style='color:gray'>tokens in use in {runtime}: " + ', '.join(in_use_token_names) + "</span>")
    return selected_tokens, token_loader, tokens

def show_k8s_context(cont, show_link=True) -> bool:
    app = AppSettings.load_static()
    cont.markdown(f'#### Target Kubernetes Context')
    context, server_url = K8sSettings.get_current_k8s_context_name()
    if not context or not server_url:
        cont.warning(f"Context and Server URL cant be detected from k8s config: {K8sSettings.kube_config_path}")
        return False

    col1b, col2b, col2c = cont.columns([1, 1, 1])
    col1b.markdown(f"Kubernetes cluster context: `{context}` ")
    l = "[Change Context](/Settings?tab=k8s)" if show_link else ""
    col2b.markdown(f"Server URL: `{server_url}` {l}")
    col2c.markdown(f"namespace: `{app.k8s_namespace}`")
    return True