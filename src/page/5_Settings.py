import os
from time import sleep
import re

import streamlit as st
import streamlit.components.v1 as components

from src.page.ui_lib.login_manager import LoginManager
from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.pat_tokens_ui import add_pat_token_dialog, remove_pat_token_dialog, show_change_site_dialog
from src.page.ui_lib.shared_bridge_settings import show_k8s_context
from src.page.ui_lib.shared_ui import SharedUi
from src.page.ui_lib.stream_logger import StreamLogger
from src.cli import version_check
from src.cli.app_config import APP_CONFIG, APP_NAME_FOLDER
from src.ecr_registry_private import EcrRegistryPrivate
from src.enums import ADMIN_PAT_PREFIX
from src.github_version_checker import GithubVersionChecker
from src.k8s_client import K8sSettings
from src.lib.general_helper import FileHelper, StringUtils
from src.lib.usage_logger import USAGE_LOG, UsageMetric
from src.models import AppSettings
from src.token_loader import TokenLoader, token_file_path


def render_auth_tokens_tab(tab):
    tab.subheader("Tableau Cloud Token Authentication")
    tab.info(f"BridgeCTL uses Personal Access Tokens to authenticate bridge agents to Tableau Cloud. See [Tableau Cloud Documentation - Personal Access Tokens](https://help.tableau.com/current/server/en-us/security_personal_access_tokens.htm).")
    token_loader = TokenLoader(StreamLogger(st.container()))
    if not os.path.exists(token_file_path):  # create empty file if it doesn't exist, so that TokenLoader doesn't log a message
        token_loader.create_new()

    # STEP - Show tokens and warnings
    bst = token_loader.load()
    token_names = [x.name for x in bst.tokens]
    c1,c2 = tab.columns([1,3])
    if bst.site.sitename:
        c1.markdown(f"**Tokens added for site `{bst.site.sitename}`**")
        if c2.button("Change Site"):
            show_change_site_dialog(token_loader)
        tokens_display = ', '.join([f"{t.name}" for t in bst.tokens])
        tab.markdown(f"`{tokens_display}`")
    have_admin_pat =  any(t.startswith(ADMIN_PAT_PREFIX) for t in token_names)
    if not have_admin_pat:
        tab.warning(f"Note: You have not yet added a Token starting with '{ADMIN_PAT_PREFIX}'.")
    else:
        have_bridge_token = any(not t.startswith(ADMIN_PAT_PREFIX) for t in token_names)
        if not have_bridge_token:
            tab.warning(f"Note: You have not yet added a PAT Token that does NOT start with '{ADMIN_PAT_PREFIX}', this token will be used to run a Bridge agent. This token can have any name you choose.")

    # STEP - Show Add button
    if tab.button("Add Token"):
        add_pat_token_dialog(bst, token_loader)
    if tab.button("Remove Token"):
        remove_pat_token_dialog(bst, token_loader)
    # if tab.button("Import"):
    #     render_bulk_mode_dialog()

def get_uploader_key():
    if "file_uploader_key" not in st.session_state:
        st.session_state["file_uploader_key"] = 0
    return st.session_state["file_uploader_key"]

class SessionUploadK8sConfig:
    default = "default"
    upload = "upload"

    @staticmethod
    def get():
        if 'upload_k8s_mode' not in st.session_state:
            st.session_state.upload_k8s_mode = SessionUploadK8sConfig.default
        return st.session_state.upload_k8s_mode

    @staticmethod
    def set(mode):
        st.session_state.upload_k8s_mode = mode

def validate_k8s_namespace(namespace, col1):
    if not namespace:
        col1.warning("Namespace is required")
        return False
    pattern = r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
    if not re.match(pattern, namespace):
        col1.text(f"Invalid namespace. Must match pattern: {pattern}")
        return False
    return True


def render_k8s_tab(tab_k8s):
    tab_k8s.subheader("Kubernetes")
    app = AppSettings.load_static()
    col1, col2 = tab_k8s.columns(2)

    is_k8s_enabled = col1.checkbox("Enable Kubernetes integration", app.feature_k8s_enabled, help="This will enable Kubernetes integration.")
    if app.feature_k8s_enabled != is_k8s_enabled:
        app.feature_k8s_enabled = is_k8s_enabled
        app.save()
        st.rerun()
    tab_k8s.write("")
    tab_k8s.write("")
    if not app.feature_k8s_enabled:
        return
    # col1.info("Kubernetes enabled.")
    # config_type = col1.radio("Kubernetes Context", ["default", "local"], index=0)
    if not K8sSettings.does_kube_config_exist():
        SessionUploadK8sConfig.set(SessionUploadK8sConfig.upload)

    if SessionUploadK8sConfig.get() == SessionUploadK8sConfig.default:
        if K8sSettings.does_kube_config_exist():
            col1.markdown(f"A valid kube_config file found in the config folder. `{K8sSettings.kube_config_path}`")
            if not show_k8s_context(col1, False):
                return
        else:
            col1.warning(f"A valid kube_config file not found at `{K8sSettings.kube_config_path}`")

        if col1.button("Change kube_config"):
            SessionUploadK8sConfig.set(SessionUploadK8sConfig.upload)
            st.rerun()

        selected_namespace = col1.columns(2)[0].text_input("Target namespace for bridge pods", app.k8s_namespace, help="Tableau Bridge pods will be deployed to this namespace.")
        if selected_namespace != app.k8s_namespace:
            if validate_k8s_namespace(selected_namespace, col1):
                app.k8s_namespace = selected_namespace
                app.save()
                col1.success("k8s namespace saved")
    elif SessionUploadK8sConfig.get() == SessionUploadK8sConfig.upload:
        # col1.info("Change Kube Config")
        e = " The current kube config file will be backed up to ~/.kube/config.bak"  if K8sSettings.does_kube_config_exist() else ""
        col1.info(f"To authenticate to your kubernetes cluster, please upload the kube config yaml file. This will be stored at ~/.kube/config.{e}")
        kube_config = col1.file_uploader('Upload kube config file',
                accept_multiple_files=False,
                key=get_uploader_key())
        cancel_button_label = "Cancel"
        if kube_config is not None:
            st.session_state["file_uploader_key"] += 1
            value = kube_config.getvalue()
            error_msg = FileHelper.validate_yaml(value)
            if error_msg:
                col1.warning(f"Invalid yaml file. Error:\n\n{error_msg}")
            else:
                K8sSettings.backup_kube_config()
                K8sSettings.save_kube_config(value)
                col1.success("kube config file uploaded")
                SessionUploadK8sConfig.set(SessionUploadK8sConfig.default)
                cancel_button_label = "Refresh 🔄"
                if not show_k8s_context(col1, False):
                    return

        if col1.button(cancel_button_label):
            SessionUploadK8sConfig.set(SessionUploadK8sConfig.default)
            st.rerun()

def save_ecr_settings(form, app, account_id, repo_name, region):
    pattern_id = r'^\d{12}$' # Regular expression to match a 12-digit number
    if not re.match(pattern_id, str(account_id)):
        form.warning("AWS Account ID must be 12 digits")
        return
    pattern_repo = r'^[a-z]([a-z0-9\-_./]{0,254}[a-z0-9])?$' # Regular expression to match the repository name rules
    if not(2 <= len(repo_name) <= 256 and re.match(pattern_repo, repo_name)): # Ensure length is within the valid range and match pattern
        form.warning(f"Repository Name should match `{pattern_repo}`")
        return
    pattern_region = r'^[a-z]{2}-[a-z]+-\d$'
    if not re.match(pattern_region, region):
        form.warning(f"Region must match '{pattern_region}'")
        return
    if account_id == app.ecr_private_aws_account_id and repo_name == app.ecr_private_repository_name and region == app.aws_region:
        form.warning("No change")
        return
    app.ecr_private_aws_account_id = account_id
    app.ecr_private_repository_name = repo_name
    app.aws_region = region
    app.save()
    form.success("settings saved")
    sleep(2)
    st.rerun()

def render_container_registry_tab(tab_registry):
    tab_registry.subheader("Container Registry")
    app = AppSettings.load_static()

    tab_registry.info("Instructions: Enter the information about your private AWS ECR repository. "
    "You can find the URI of your Private ECR Repository in the [AWS ECR Console](https://us-west-2.console.aws.amazon.com/ecr/private-registry/repositories). \n\n"
    "Example: *123456789012.dkr.ecr.us-west-2.amazonaws.com/my-repository*, where *123456789012* is the AWS AccountID and *my-repository* is the ECR Repository name.\n\n"
    "Note that in order to use ECR, you need to have the [AWS CLI](https://aws.amazon.com/cli) installed locally and configured with the correct [authentication credentials](https://stackoverflow.com/questions/44243368/how-to-login-with-aws-cli-using-credentials-profiles).")

    col1, col2 = tab_registry.columns(2)
    col1.markdown("#### AWS Private ECR Repository")
    is_ecr_enabled = col1.checkbox("Enable AWS ECR", app.feature_ecr_enabled, help="Enable AWS ECR integration.")
    if app.feature_ecr_enabled != is_ecr_enabled:
        app.feature_ecr_enabled = is_ecr_enabled
        app.save()
        st.rerun()
    if app.feature_ecr_enabled:
        form = col1.form(key="cont_reg")
        account_id = StringUtils.val_or_empty(form.text_input("AWS AccountID", app.ecr_private_aws_account_id))
        repo_name = StringUtils.val_or_empty(form.text_input("Private ECR Repository Name", app.ecr_private_repository_name))
        region = StringUtils.val_or_empty(form.text_input("AWS Region", app.aws_region))
        reg = EcrRegistryPrivate(StreamLogger(form), account_id, repo_name, region)
        form.markdown(f"Full URL: `{reg.get_repo_url()}`")

        if form.form_submit_button("Save"):
            save_ecr_settings(form, app, account_id, repo_name, region)

        if tab_registry.button("Validate Connection to ECR"):
            is_success, error = reg.check_connection_to_ecr() #FutureDev: make error message better
            if is_success:
                tab_registry.success("Connection to ECR successful")
            else:
                tab_registry.error(f"Error: {error}")

def render_updates_tab(tab_updates):
    tab_updates.subheader("App Updates")
    app = AppSettings()
    app.load()
    col1, col2 = tab_updates.columns(2)
    if APP_CONFIG.is_devbuilds():
        from src.internal.devbuilds.devbuilds_const import DevBuildsLinks
        release_notes_url = DevBuildsLinks.wiki_docs
    else:
        release_notes_url = "https://github.com/tableau/bridgectl/blob/main/RELEASE_NOTES.md"
    space = "&nbsp;" * 50
    col1.info(f"Current BridgeCTL version: {APP_CONFIG.app_version} {space} [release notes]({release_notes_url})")
    SharedUi.show_app_version(tab_updates, True)

    url = GithubVersionChecker.get_releases_home()
    if col1.button(f"Check for App Updates"):
        cont = col1.container(border=True)
        cont.write(f"Checking for newer [bridgectl release]({url})")
        latest_ver_msg, latest_ver = version_check.check_latest_and_get_version_message()
        latest_ver_msg = latest_ver_msg.replace("[green]", "").replace("[/green]", "").replace("[red]", "").replace("[/red]", "").replace("[blue]", "").replace("[/blue]", "")
        cont.text(f"Latest version: {latest_ver} \n\n {latest_ver_msg}")
        if "new version" in latest_ver_msg:
            cont.text(f"To update, run `{APP_NAME_FOLDER}` from the command-line")
        USAGE_LOG.log_usage(UsageMetric.settings_chk_updates)
    tab_updates.markdown("")
    cont = tab_updates.columns(2)[0].container(border=True)
    LoginManager.update_login(app, cont)


    # if tab_updates.button(f"Docker Info"):
    #     from src.docker_client import DockerClient
    #     doc_client = DockerClient(StreamLogger(st.container()))
    #     info = doc_client.get_docker_info()
    #     tab_updates.text(info)

def render_features_tab(tab_features):
    tab_features.subheader("Features")
    app = AppSettings.load_static()
    enable_test_features = tab_features.checkbox("Enable Additional Pages", value=app.feature_additional_pages_enabled)
    tab_features.markdown("- **Test Bridge** page provides an easy way to kick off extract refresh jobs and test that bridge agents are correctly configured.")
    tab_features.markdown("- **Jobs** page shows the status of extract refresh jobs.")
    tab_features.markdown("- **Example Scripts** page shows example bash scripts for building and running bridge containers.")
    tab_features.markdown("- **Monitor** page allows you to receive alerts via slack or pager duty if a bridge agent becomes disconnected.")
    if app.feature_additional_pages_enabled != enable_test_features:
        app.feature_additional_pages_enabled = enable_test_features
        app.save()
        st.rerun()
    if APP_CONFIG.is_devbuilds():
        is_disabled = False
        if app.streamlit_server_address != "localhost":
            tab_features.warning(f"Hammerhead can only be enabled when streamlit_server_address = 'localhost'")
            is_disabled = True
        enable_hammerhead_features = tab_features.checkbox("Enable Hammerhead Pages", value=app.feature_hammerhead_enabled, disabled=is_disabled)
        tab_features.markdown("- **Hammerhead** pages provide an easy way to report and modify your Hammerhead EC2 instances.")
        if app.feature_hammerhead_enabled != enable_hammerhead_features:
            app.feature_hammerhead_enabled = enable_hammerhead_features
            app.save()
            st.rerun()

def show_toast_after_refresh():
    if 'show_toast' in st.session_state and st.session_state.show_toast:
        st.toast(str(st.session_state.show_toast))
        st.session_state.show_toast = False

def select_tab_from_query_param():
    """
    Look-up the tab from the query-string and click that tab
    """
    query_param = st.query_params.get("tab")
    if not query_param:
        return
    tab_mapping = {
        "tokens": 0,
        "k8s": 1,
        "registry": 2,
        "features": 3,
        "updates": 4
    }
    # ref: https://discuss.streamlit.io/t/how-to-bring-the-user-to-a-specific-tab-within-a-page-in-my-multipage-app-using-the-url/42796/7
    index_tab = tab_mapping.get(query_param)
    js = f"""
    <script>
        var tab = window.parent.document.getElementById('tabs-bui1-tab-{index_tab}');
        tab.click();
    </script>
    """
    if index_tab:
        components.html(js) # ref: https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html

def page_content():
    tab_pats, tab_k8s, tab_registry, tab_features, tab_updates  = st.tabs(["Token Authentication", "Kubernetes", "Container Registry", "Features", "App Updates"])
    # if 'view_mode' not in st.session_state:
    #     st.session_state.view_mode = ViewMode.view_mode
    show_toast_after_refresh()
    render_auth_tokens_tab(tab_pats)
    render_k8s_tab(tab_k8s)
    render_container_registry_tab(tab_registry)
    render_features_tab(tab_features)
    render_updates_tab(tab_updates)
    select_tab_from_query_param()

# if __name__ == "__main__":
PageUtil.set_page_config(page_title="Settings", page_header="Settings")
page_content()

