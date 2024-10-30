from tabulate import tabulate

from src.lib.tc_api_client import TableauCloudLogin, TCApiClient, TCApiLogic
from src.lib.tc_api_client_jobs import TCApiClientJobs
from src.models import PatToken
from src.token_loader import TokenLoader


def get_or_fetch_site_id(api: TCApiClient, token: PatToken, logger) -> str:
    ### get site id from token or fetch from API.
    ###
    if not token.site_id or not token.site_luid or not token.user_email:
        ret = api.get_session_info()
        token.site_id = ret['result']['site']['id']
        token.site_luid = ret['result']['site']['luid']
        token.user_email = ret['result']['user'].get('username')
        TokenLoader(logger).update_token_site_ids(token.site_id, token.site_luid, token.user_email)
    return token.site_id


def dict_to_str(d):
    out = []
    for key, value in d.items():
        out.append(f"{key}: {value}")
    return "\n".join(out)


def display_bridge_status(token: PatToken, logger, data_only: bool = False):
    login_result = TableauCloudLogin.login(token, True)
    logic = TCApiLogic(login_result)
    site_id = get_or_fetch_site_id(logic.api, token, logger)
    try:
        rows = logic.get_bridge_status(site_id)
        headers = ["Agent Name", "Pool", "Owner", "Version", "Connection Status", "Last Connected"] #, "Needs Upgrade", "ExtractCnt"]
        if data_only:
            return rows, headers
        return tabulate(rows, headers=headers)
    finally:
        TableauCloudLogin.logout(token.get_pod_url(), login_result.session_token)


class BridgeStatusLogic:
    def __init__(self, logger):
        self.logger = logger

    def show_jobs_report(self, token: PatToken, logger, just_fetch=True, jobs_details_amount=0):
        login_result = TableauCloudLogin.login(token)
        if not login_result.is_success:
            raise Exception(f"Login failed: {login_result.error}")

        try:
            api = TCApiClientJobs(login_result)
            site_id = get_or_fetch_site_id(api, token, logger)
            # jobs = api.get_jobs(site_id)
            jobs = api.get_jobs_sorted(site_id)
            if just_fetch:
                if jobs_details_amount > 0:
                    for job in jobs['result']['backgroundJobs'][:jobs_details_amount]:
                        job["jobDetails"] = dict_to_str(self.get_job_details(token, job["jobId"]))
                    for job in jobs['result']['backgroundJobs'][jobs_details_amount:]:
                        job["jobDetails"] = ""
                return jobs

            ms = ""
            if "moreItems" in jobs['result']:
                if jobs['result']['moreItems']:
                    ms = ' (more)'
                tc = jobs['result']['totalCount']
                self.logger.info(f"total records: {tc}{ms}")
                self.print_jobs_as_table(jobs)
            else:
                self.logger.info("invalid format")
            return jobs
        finally:
            TableauCloudLogin.logout(token.get_pod_url(), login_result.session_token)

    def get_job_details(self, token: PatToken, job_id: str):
        login_result = TableauCloudLogin.login(token)
        if not login_result.is_success:
            raise Exception(f"Login failed: {login_result.error}")

        try:
            api = TCApiClientJobs(login_result)
            return api.get_job_detail(job_id).get("result")
        finally:
            TableauCloudLogin.logout(token.get_pod_url(), login_result.session_token)

    def print_jobs_as_table(self, jobs: dict):
        # background_jobs = jobs_result.jobs["backgroundJobs"]["backgroundJob"]
        background_jobs = jobs["result"]["backgroundJobs"]

        headers = ["ID", "Status", "Priority", "Task Type", "Requested Time", "Current Run time", "Description" ]

        # table_data = [
        #     [job["id"], job["status"], job["createdAt"], job["priority"], job["jobType"]]
        #     for job in background_jobs
        # ]
        table_data = [
            ['_' + job["jobId"], job["status"], job["priority"], job["taskType"],job["jobRequestedTime"],job["currentRunTime"], job["jobDescription"].replace('Bridge Client: ','')]
            for job in background_jobs
        ]
        self.logger.info(tabulate(table_data, headers=headers))

    def show_jobs_report_public(self, token: PatToken):
        login_result = TableauCloudLogin.login(token)
        try:
            api = TCApiClientJobs(login_result)
            jobs = api.get_jobs_public()
            return jobs
        finally:
            TableauCloudLogin.logout(token.get_pod_url(), login_result.session_token)

    def remove_agent(self, token, agent_name, agent_sitename, logger):
        login_result = TableauCloudLogin.login(token, True)
        api = TCApiClient(login_result)
        site_id = get_or_fetch_site_id(api, token, logger)
        if token.sitename != agent_sitename and agent_sitename:
            self.logger.warning(f"token sitename {token.sitename} is different from the agent label sitename '{agent_sitename}', you'll need to manually remove the agent from the Tableau cloud bridge settings page.")
            return False
        settings = api.get_bridge_settings(site_id)
        for a in settings['result']['siteAdminBridgeSettings']['remoteAgentSettings']['agents']:
            if a['agentName'] == agent_name:
                device_id = a['deviceId']
                owner_id = a['ownerId']
                api.delete_bridge_agent(owner_id, device_id)
                self.logger.info(f"removed Tableau Cloud Bridge Agent: {agent_name}")
                return True
        self.logger.warning(f"agent name '{agent_name}' not found when calling Tableau Cloud API.")
        return False
