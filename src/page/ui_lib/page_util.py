import streamlit as st
import streamlit.components.v1 as components


from streamlit.source_util import (
    get_pages,
    _on_pages_changed
)

from src.cli.app_config import APP_CONFIG
from src.enums import ContainerRepoURI
from src.lib.general_helper import StringUtils
from src.models import LoggerInterface
from src.token_loader import TokenLoader


class PageUtil:
    REPORT_PAGE_NAMES = ["Jobs", "Agent_Status"]
    MAIN_SCRIPT_PATH_STR = "Home.py"
    K8S_PAGE_NAMES = ["Kubernetes_-_Run_Bridge", "Kubernetes_-_Manage_Bridge"]
    WEB_ONLY_PAGE = "Web"
    DATACONNECT_PUBLISH_PAGE = ["Data_Connect_-_Base_Image"]
    PUBLISH_IMAGE_PAGE = ["Publish_Image"]
    ADDITIONAL_PAGES = ["Test_Bridge", "Jobs", "Example_Scripts", "Monitor"]
    HAMMERHEAD_PAGES = ["Hammerhead_-_Auth", "Hammerhead_-_Report", "Hammerhead_-_Create", "Hammerhead_-_Modify"]
    # MONITOR_PAGE = "Monitor"
    # LOGS_GPT_PAGE = "Logs_GPT"

    @staticmethod
    def set_page_config(page_title: str, page_header: str, skip_image: bool = False):
        title =  f"{page_title}"  if page_title else "Tableau Bridge"
        st.set_page_config(
            page_title=title,
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.write(f"# {page_header}")
        if skip_image:
            return
        app_title_image = "src/page/assets/tableau_icon_24.png"
        st.logo(app_title_image)

    @staticmethod
    def image_handler():
        js = f"""
            <script>
                
                setTimeout(() => {{
                    const crossButton = window.parent.document.querySelector("[data-testid='baseButton-header']")
                        crossButton.addEventListener("click", () => {{
                            setTimeout(() => {{
                                const arrowButton = window.parent.document.querySelector("[data-testid='baseButton-headerNoPadding']")
                                arrowButton.addEventListener("click", () => {{
                                    window.parent.document.getElementsByClassName("bottom-left-content")[0].style.display = "";
                                }})
                                window.parent.document.getElementsByClassName("bottom-left-content")[0].style.display = "none";
                            }}, 200)
                        }});
                }}, 500)
            </script>
        """
        components.html(js)

    @staticmethod
    def horizontal_radio_style():
        # st.markdown("""<style>div.row-widget.stRadio > div{flex-direction:row;}</style>""", unsafe_allow_html=True)
        st.html(
            """<style>div[data-testid="stRadio"] > div {
                    display: flex;
                    flex-direction: row;
                }
                div[data-testid="stRadio"] label {
                    margin-right: 1rem;
                }</style>
                """)

    @classmethod
    def remove_all_pages_except_web(cls):
        current_pages = get_pages(PageUtil.MAIN_SCRIPT_PATH_STR)
        keys_to_check = list(current_pages.keys())
        for key in keys_to_check:
            if current_pages[key]['page_name'] not in [cls.WEB_ONLY_PAGE]:
                del current_pages[key]
        _on_pages_changed.send()

    @staticmethod
    def get_base_image_examples():
        base_image_examples = ", ".join(StringUtils.get_values_from_class(ContainerRepoURI))
        if APP_CONFIG.is_devbuilds():
            from src.internal.devbuilds.devbuilds_const import ReposDev
            base_image_examples += f", {ReposDev.sfdc_rhel9}"
        return base_image_examples

    @staticmethod
    def get_admin_pat_or_log_error(logger: LoggerInterface):
        token = TokenLoader(logger).get_token_admin_pat()
        if not token:
            logger.warning("You can add PAT tokens on the [Settings page](/Settings)")
            return None
        return token