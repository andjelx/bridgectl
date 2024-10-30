import re

import pandas as pd
import streamlit as st
from datetime import datetime

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.stream_logger import StreamLogger
from src.cli.bridge_status_logic import BridgeStatusLogic
from src.token_loader import TokenLoader


JOBS_DETAILS_TO_SHOW = 5

def convert_to_locale_datetime(iso_str):
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime('%c')

def page_content():
    s_logger = StreamLogger(st.container())
    c1, c2 = st.columns(2)
    with st.spinner("Jobs Report..."):
        token = TokenLoader(s_logger).get_token_admin_pat()
        if not token:
            st.warning("Please Configure Tokens in order to call Tableau Cloud APIs")
            return
        c1.markdown(f"[Tableau Cloud Jobs Report]({token.get_pod_url()}/#/site/{token.sitename}/jobs) for site `{token.sitename}`" )
        show_job_details = c1.checkbox(f"include details")
        c2.button("🔄")
        jobs_details_num = 0
        if show_job_details:
            c2.markdown(f"Showing details for the {JOBS_DETAILS_TO_SHOW} most recent jobs")
            jobs_details_num = JOBS_DETAILS_TO_SHOW

        logic = BridgeStatusLogic(s_logger)
        jobs_report = logic.show_jobs_report(token, s_logger,True, jobs_details_num)
        try:
            jobs = jobs_report['result']['backgroundJobs']
        except KeyError:
            jobs = None
        if not jobs:
            st.warning("No Jobs Found")
            return

        cols = {
            'jobId': 'ID',
            'status': 'Status',
            # 'priority': 'Priority',
            'taskType': 'Task Type',
            'jobRequestedTime': 'Job Requested Time',
            'currentRunTime': 'RunTime',
            'currentQueueTime': 'QueueTime',
        }
        if 'jobDescription' in jobs[0]:
            cols['jobDescription'] = 'Description'
        if show_job_details:
            cols['jobDetails'] = 'Job Details'
            cols['contentName'] = 'Content Name'
            for j in jobs: # populate the contentName field from jobDetails
                if j['jobDetails']:
                    match = re.search(r"contentName:\s*(\S+)", j['jobDetails'])
                    j["contentName"] = match.group(1) if match else ""
                else:
                    j["contentName"] = ""
        jobs_df = pd.DataFrame(jobs)
        jobs_df = jobs_df.rename(columns=cols)
        order = [v for k, v in cols.items()]
        jobs_df = jobs_df[order]
        jobs_df['Status'] = jobs_df['Status'].replace('Completed', '✅ Sent to Bridge')
        jobs_df['Status'] = jobs_df['Status'].replace('BridgeExtractionCompleted', '✅ Completed')
        jobs_df['Status'] = jobs_df['Status'].replace('Failed', '❗ Failed')
        jobs_df['Status'] = jobs_df['Status'].replace('Pending', '🕒 Pending')
        jobs_df['Status'] = jobs_df['Status'].replace('InProgress', '🔄 In Progress')
        #jobs_df['Job Requested Time'] = jobs_df['Job Requested Time'].apply(convert_to_locale_datetime)
        st.dataframe(jobs_df, hide_index=True, use_container_width=True, height=1000)


PageUtil.set_page_config("Jobs", "Jobs")
page_content()
