import pandas as pd
import streamlit as st

from src.page.ui_lib.pat_tokens_ui import show_change_site_dialog
from src.page.ui_lib.stream_logger import StreamLogger

from src.page.ui_lib.page_util import PageUtil
from src.cli import bridge_status_logic
from src.token_loader import TokenLoader


def page_content():
    with st.spinner("Fetching status..."):
        try:
            s_logger = StreamLogger(st.container())
            token_loader = TokenLoader(s_logger)
            admin_token = token_loader.get_token_admin_pat()
            if not admin_token:
                return
            st.markdown(f"Tableau Cloud [Bridge Status]({admin_token.get_pod_url()}/#/site/{admin_token.sitename}/bridge) for site `{admin_token.sitename}`")
            if token_loader.have_additional_token_yml_site_files():
                if st.button("Change Site"):
                    show_change_site_dialog(token_loader)

            agents_status, headers = bridge_status_logic.display_bridge_status(admin_token, s_logger, True)
            df = pd.DataFrame(agents_status, columns = headers)
            s_col = 'Connection Status'
            df[s_col] = df[s_col].replace('CONNECTED', '✅ Connected')
            df[s_col] = df[s_col].replace('DISCONNECTED', '❌ Disconnected')
            height = len(df) * 40 + 20
            st.dataframe(df, hide_index=True, height=height)

        except Exception as ex:
            st.text(f"Error fetching status: {ex}")

PageUtil.set_page_config("Status", "Bridge Agent Status")
page_content()
