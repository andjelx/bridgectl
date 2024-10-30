import re
from time import sleep

import streamlit as st

from src.page.ui_lib.stream_logger import StreamLogger
from src.enums import ADMIN_PAT_PREFIX
from src.lib.general_helper import StringUtils
from src.lib.tc_api_client import TCApiLogic, TableauCloudLogin
from src.models import PatToken, BridgeSiteTokens
from src.token_loader import TokenLoader


def validate_token(t_name, t_secret, t_site_name, t_pod_url):
    if not t_name:
        st.warning("token name is required")
        return None
    if not t_name.startswith(ADMIN_PAT_PREFIX):
        pattern = r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$"
        if not re.match(pattern, t_name):
            st.warning(f"PAT Token name `{t_name}` is not valid, must match this pattern `{pattern}` since the docker container uses the same name.")
            return None
        #("Invalid container name (bridge_fluke23_local 16), only [a-zA-Z0-9][a-zA-Z0-9_.-] are allowed")
    token_loader = TokenLoader(StreamLogger(st.container()))
    existing_token = token_loader.get_token_by_name(t_name, False)
    if existing_token:
        st.warning(f"token with name '{t_name}' already exists")
        return None
    if not t_secret:
        st.warning("token secret is required")
        return None
    if not t_site_name:
        st.warning("Sitename is required")
        return None
    error = StringUtils.is_valid_pat_url(t_pod_url)
    if error:
        st.warning(f"Invalid Tableau Online Server URL. {error}")
        return None
    new_token = PatToken(t_name, t_secret, t_site_name, t_pod_url)
    with st.spinner(""):
        try:
            login_result = TableauCloudLogin.login(new_token, False)
        except Exception as ex:
            st.warning(f"Error logging in to Tableau Cloud APIS with token. {ex}")
            return None
        if not login_result.is_success:
            st.warning("INVALID PAT token. Unable to login to Tableau Cloud APIS with token.")
            return None
        logic = TCApiLogic(login_result)
        is_success, error = logic.does_token_have_site_admin_privileges()
        if not is_success:
            st.warning(f"PAT token is not SiteAdministrator. {error}")
            return None
        if new_token.is_admin_token():
            new_token.site_luid = login_result.site_luid
        logic.api.logout()
    return new_token


@st.dialog("Add Token", width="large")
def add_pat_token_dialog(bst: BridgeSiteTokens, token_loader):
    st.info("Instructions: \n"
    f"- Add one PAT token starting with '{ADMIN_PAT_PREFIX}', for example 'admin-pat-1' so that BridgeCTL can call Tableau Cloud APIs. This will enable the Jobs and Status pages and enable selection of a bridge pool on the Run page. \n"
    f"- Also add one PAT token for each bridge agent you wish to spin up in docker or kubernetes. These tokens can have any name. The bridge agent will be created with the same name as the selected token. Note that tokens starting with '{ADMIN_PAT_PREFIX}' cannot be used in bridge agents.\n"
    "- The PAT token should have SiteAdministrator permissions. \n"
    "- The tokens will be stored in `bridgectl/config/tokens.yml`")
    if not bst:
        bst = token_loader.load()
    if len(bst.tokens) > 0:
        # last_t :PatToken = tokens[-1]
        default_sitename = bst.site.sitename
        default_server_url = bst.site.pod_url
        new_site = st.columns([3,1])[1].checkbox("Add New Site", help=f"Check this box if you are adding a new Tableau Cloud Site (a site other than `{default_sitename}`)")
        if new_site:
            default_sitename = ""
            default_server_url = ""
    else:
        default_sitename = ""
        default_server_url = ""
        new_site = True
        last_t = None

    with st.form(key="add_pat"):
        t_name = st.text_input("PAT Token Name", help="Name of PAT token, for example `admin-pat-1` or `blue` or `yellow`")
        t_secret = st.text_input("PAT Token Secret")
        t_site_name = st.text_input("Tableau Online Site Name", default_sitename, help="Tableau Online Site Name, for example `mysite`", disabled=not new_site)
        t_site_name = t_site_name.lower() # some auth fails when site_name is uppercase.
        t_pod_url = st.text_input("Tableau Online Server URL", default_server_url, help="Tableau Online URL, for example `https://prod-useast-a.online.tableau.com`", disabled=not new_site)
        if st.form_submit_button("Add PAT"):
            new_token = validate_token(t_name, t_secret, t_site_name, t_pod_url)
            if new_token:
                if new_site and len(bst.tokens) > 0:
                    if t_site_name == bst.site.sitename:
                        st.warning(f"`{t_site_name}` is the same site. Please uncheck 'Add New Site'")
                        return
                    if token_loader.check_file_exists(t_site_name):
                        st.warning(f"tokens for site `{t_site_name}` already exists. Please use the 'Change site' dialog, then add more tokens for the site.")
                        return
                    token_loader.rename_token_file_to_site(bst.site.sitename)
                    token_loader.create_new()
                token_loader.add_token(new_token)
                st.session_state.show_toast = f"token {t_name} added"
                st.rerun()

@st.dialog("Remove Token", width="large")
def remove_pat_token_dialog(bst: BridgeSiteTokens, token_loader):
    if not bst:
        bst = token_loader.load()
    st.info("Select one or more PAT tokens to remove from `bridgectl/config/tokens.yml`")
    token_names = [x.name for x in bst.tokens]
    selected_token_names = st.multiselect("Select tokens to remove", token_names)
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    st.text("")
    is_enabled = bool(selected_token_names)
    if st.button("Remove PAT", disabled=(not is_enabled)):
        removed_tokens = []
        for selected_token_name in selected_token_names:
            removed_tokens.append(selected_token_name)
            token_loader.remove_token(selected_token_name)
            # st.success(f"token {selected_token_name} removed")
        st.session_state.show_toast = f"tokens removed: {', '.join(removed_tokens)}"
        st.rerun()

@st.dialog("Bulk Import PAT tokens", width="large")
def render_bulk_mode_dialog():
    form = st.form(key="import_settings")
    form.info("""To bulk Import PAT Tokens, please use the following YAML format.\n
```
tokens:
    - name: tokenname1
      secret: xxxxx
    - name: tokenname2
      secret: xxxx
site:
    server_url: prod-useast-a.online.tableau.com
    site_name: mysite123
```
      """) #You can manually create the tokens and enter them or use the Chrome extension found in the `bridgectl/src/bulk` folder

    token_import_yaml = form.text_area("", height=250)
    cols_s = form.columns([1, 1, 3])
    if cols_s[0].form_submit_button("Import"):
        if not token_import_yaml:
            st.warning("Please enter PAT tokens in valid YAML format")
        else:
            logger = StreamLogger(form)
            count_imported = TokenLoader(logger).merge_token_yaml(token_import_yaml)
            form.success(f"Bulk imported {count_imported} tokens")

@st.dialog("Change Tableau Cloud Site")
def show_change_site_dialog(token_loader: TokenLoader):
    st.info("BridgeCTL allows you to work with multiple Tableau Cloud sites. "
            "You can switch between sites by selecting a site from the dropdown below. "
            "This list is stored in the tokens_{sitename}.yml file in the `bridgectl/config` directory. "
            "You can add a new site by adding a PAT token for a different site.")
    bst = token_loader.load()
    st.markdown(f"Current site name: `{bst.site.sitename}`")
    site_list = token_loader.get_token_yml_site_list()
    if not site_list:
        st.info("No other sites found. You can add additional sites by adding a Token and selecting 'Add New Site' checkbox.")
        return
    selected_site = st.selectbox("Change to Site:", site_list)
    if st.button("Change Site", key="cng_site"):
        # STEP: Swap tokens.yml files to be the currently selected file.
        token_loader.rename_token_file(bst.site.sitename, selected_site)
        st.success(f"Site changed to {selected_site}")
        sleep(1)
        st.rerun()
