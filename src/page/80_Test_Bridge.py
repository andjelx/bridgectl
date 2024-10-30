import dataclasses

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.stream_logger import StreamLogger
from src.cli.bridge_status_logic import get_or_fetch_site_id
from src.lib.tc_api_client import TableauCloudLogin, TCApiLogic
from src.lib.tc_api_client_jobs import TCApiClientJobs

import streamlit as st

from src.token_loader import TokenLoader

@dataclasses.dataclass
class TaskName:
    id: str
    target_name: str = None
    target_id: str = None


def get_tasks(sl: StreamLogger, col1):
    token = TokenLoader(sl).get_token_admin_pat()
    if not token:
        col1.warning("You can add PAT tokens on the [Settings page](/Settings)")
        return None, None

    tasks_link = f"{token.get_pod_url()}/#/site/{token.sitename}/tasks/extractRefreshes"
    col1.markdown(f"[Tableau Cloud Extract Refresh Tasks]({tasks_link})")
    col1.markdown("")
    with st.spinner("Fetching Extract Refresh Tasks..."):
        # req = bridge_settings_file_util.load_settings()
        login_result = TableauCloudLogin.login(token, True)
        logic = TCApiLogic(login_result)
        logger = StreamLogger(st.container())
        site_id = get_or_fetch_site_id(logic.api, token, logger)

        api = TCApiClientJobs(login_result)
        tasks = api.get_tasks(site_id)
        task_names = []
        if tasks:
            for t in tasks["result"]["tasks"]:
                name = f"workbook {t['targetId']}" if t['targetType'] == "Workbook" else t['datasource_name']
                task_names.append(TaskName(id=t["id"], target_name=name, target_id=t['targetId']))
            for t in tasks["result"]["workbooks"]:
                tn = next((x for x in task_names if x.target_id == t["id"]), None)
                if tn:
                    tn.target_name = f"Workbook {t['name']}"

            task_names.sort(key=lambda x: x.target_name.lower())
        return task_names, api

def format_task(task):
    return task.target_name

def page_content():
    st.info("""**Instructions:** This page will help to ensure that bridge agents are correctly configured by starting Extract Refresh Jobs.
After starting a task, you can see the status on the [jobs](/Jobs) page.
    """)
    col1, col2 = st.columns([1,2])
    sl = StreamLogger(st.container())
    names, api = get_tasks(sl, col1)
    if not names:
        st.warning("No extract refresh tasks found")
        return
    form = col1.form(key="start_task")
    selected = form.selectbox("Select an Extract Refresh Task", names, format_func=format_task)
    if form.form_submit_button("Start Extract Refresh Task"):
        api.start_tasks([selected.id])
        col1.success(f"Job started for {selected.target_name}")


PageUtil.set_page_config("Test", "Test Bridge Agents")
page_content()


# API Docs
# run extract refresh task
# https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_extract_and_encryption.htm#run_extract_refresh_task

# create extract refresh task
# https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_extract_and_encryption.htm#create_cloud_extract_refresh_task

# delete extract refresh task
# https://help.tableau.com/current/api/rest_api/en-us/REST/rest_api_ref_extract_and_encryption.htm#delete_extract_refresh_task


# create domain-> pool mapping
# POST https://prod-useast-a.online.tableau.com/vizportal/api/web/v1/updateEdgePool
#{
#   "method": "updateEdgePool",
#   "params": {
#     "poolId": "2162513f-6ab2-4609-92e0-8531414bc35b",
#     "displayName": null,
#     "domainChange": {
#       "change": "ADD",
#       "domainId": "test1"
#     },
#     "agentChange": null,
#     "siteId": "146911",
#     "bridgeSettingsVersion": "0"
#   }
# }
