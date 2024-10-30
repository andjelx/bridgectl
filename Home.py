import streamlit as st

from src.page.ui_lib.login_manager import LoginManager
from src.token_loader import TokenLoaderMigrate
from src.cli.app_config import APP_CONFIG
from src.models import AppSettings, APP_STATE

pages = {}
app = AppSettings.load_static()


if LoginManager.check_login(app):
    pages[""] = [
        st.Page("src/page/1_Home.py", icon=":material/home:"),
        st.Page("src/page/5_Settings.py", icon=":material/settings:"),
    ]
    pages["Bridge"] =[
        st.Page("src/page/10_Build_Bridge.py", icon=":material/build:"),
        st.Page("src/page/20_Run_Bridge.py", icon=":material/directions_run:"),
        st.Page("src/page/50_Manage Bridge.py", icon=":material/list:"),
    ]
    if app.feature_ecr_enabled:
        pages["Bridge"].append(st.Page("src/page/52_Publish_Image.py", icon=":material/publish:"))
    if app.feature_additional_pages_enabled:
        pages["Bridge"].append(st.Page("src/page/90_Example_Scripts.py", icon=":material/code:"))

    pages["Monitor"] = [
        st.Page("src/page/70_Logs.py", icon=":material/assignment:"),
        st.Page("src/page/80_Agent_Status.py", icon=":material/dashboard:"),
    ]
    if app.feature_additional_pages_enabled:
        tm = "Monitor 🟢" if app.monitor_enable_monitoring else "Monitor ⚪"
        pages["Monitor"].extend([
            st.Page("src/page/80_Test_Bridge.py", icon=":material/labs:"),
            st.Page("src/page/81_Jobs.py", icon=":material/work:"),
            st.Page("src/page/91_Monitor.py", icon=":material/monitoring:", title=tm),
        ])

    if app.feature_k8s_enabled:
        pages["Kubernetes"] = [
            st.Page("src/page/110_Kubernetes_-_Run_Bridge.py", icon=":material/grid_view:"),
            st.Page("src/page/115_Kubernetes_-_Manage_Bridge.py", icon=":material/format_list_bulleted:"),
        ]
        if app.autoscale_show_page:
            pages["Kubernetes"].append(st.Page("src/page/117_Kubernetes_Auto_Scale.py", icon=":material/unfold_more:"))

    if APP_CONFIG.is_devbuilds():
        if app.feature_hammerhead_enabled:
            pages["Hammerhead"] = [
                st.Page("src/internal/warhammer/page/119_Hammerhead_-_Auth.py", icon=":material/key:"),
                st.Page("src/internal/warhammer/page/125_Hammerhead_-_Report.py", icon=":material/description:"),
                st.Page("src/internal/warhammer/page/126_Hammerhead_-_Create.py", icon=":material/add_circle:"),
                st.Page("src/internal/warhammer/page/129_Hammerhead_-_Modify.py", icon=":material/play_arrow:"),
            ]
        if app.feature_enable_edge_network_page:
            pages["Edge"] = [
                st.Page("src/internal/gw_client/200_Edge_Network.py", icon=":material/account_tree:"),
                st.Page("src/internal/gw_client/201_RemoteCommands.py", icon=":material/monitoring:"),
            ]

    pg = st.navigation(pages)
    pg.run()

try:
    msg = TokenLoaderMigrate.migrate_tokens()
    if msg:
        st.sidebar.success(msg)
except Exception as ex:
    st.sidebar.error(f"Error migrating tokens: {ex}")

def initialize_monitoring():
    if not APP_STATE.first_app_load: #global singleton. we only want to execute this method the first time the streamlit app loads.
        return
    APP_STATE.first_app_load = False
    if app.monitor_enable_monitoring:
        print("Initializing Monitoring")
        from src.monitor.bridge_health_alerts import BRIDGE_HEALTH_MONITOR
        if not BRIDGE_HEALTH_MONITOR.check_status():
            BRIDGE_HEALTH_MONITOR.start(app)

initialize_monitoring()

