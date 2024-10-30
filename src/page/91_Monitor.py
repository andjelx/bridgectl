from time import sleep

import streamlit as st

from src.page.ui_lib.page_util import PageUtil
from src.lib.general_helper import StringUtils
from src.models import AppSettings
from src.monitor.bridge_health_alerts import BRIDGE_HEALTH_MONITOR, AgentHealthCategory
from src.validation_helper import Validation


def is_valid(email, slack_api_key, pager_duty_key, check_int):
    if email and not Validation.is_valid_email(email):
        st.warning("Invalid email")
        return False
    if not check_int:
        return False
    try:
        check_int = float(check_int)
    except ValueError:
        st.warning("check statis interval must be a number")
        return False
    if check_int < 0.1:
        st.warning("check status interval must be >= 0.1")
        return False
    if check_int > 24:
        st.warning("check status interval must <= 24")
        return False
    return True


@st.dialog("Edit Monitoring Settings", width="large")
def edit_monitoring_settings(app: AppSettings):
    slack_email = st.text_input("slack notification email:", app.monitor_slack_recipient_email)
    st.html("""<style>[title="Show password text"] {display: none;}</style>""")
    slack_api_key = st.text_input("Slack api key", app.monitor_slack_api_key, type="password", help="Enter the slack api key for your slack app.")
    pager_duty_key = st.text_input("Pager duty routing key:", app.monitor_pager_duty_routing_key, type="password")
    check_interval_hours = st.text_input("Check status every (hours):", app.monitor_check_interval_hours)
    p = ','.join(app.monitor_only_pools) if app.monitor_only_pools else ""
    selected_monitor_pools = st.text_input("Only Monitor these Pools (comma separated):", p, help="Enter names of specific pools to only monitor agents in those pools. If a monitored pool has no agents, you will also receive notification. Leave this value blank to monitor status of all agents.")
    selected_monitor_pools = [s.strip() for s in selected_monitor_pools.split(",")] if selected_monitor_pools else []

    is_disabled = True
    if is_valid(slack_email, slack_api_key, pager_duty_key, check_interval_hours):
        if (slack_api_key != app.monitor_slack_api_key
                or slack_email != app.monitor_slack_recipient_email
                or pager_duty_key != app.monitor_pager_duty_routing_key
                or check_interval_hours != app.monitor_check_interval_hours
                or selected_monitor_pools != app.monitor_only_pools):
            is_disabled = False
    if st.button("Save", disabled=is_disabled):
        app.monitor_slack_api_key = slack_api_key
        app.monitor_slack_recipient_email = slack_email
        app.monitor_pager_duty_routing_key = pager_duty_key
        app.monitor_check_interval_hours = float(check_interval_hours)
        app.monitor_only_pools = selected_monitor_pools
        app.save()
        BRIDGE_HEALTH_MONITOR.change_settings(app)
        BRIDGE_HEALTH_MONITOR.trigger_run_now()
        st.success("saved")
        st.toast("saved, press refresh to see latest status.")
        sleep(1)
        st.rerun()


def page_content():
    st.info(f"""A background job will check regularly if any of the bridge agents are not connected by calling the Tableau Cloud APIs.\n\n
If at least one bridge agent is not status=connected, a notification will be sent via Slack and Pager Duty, if configured.""")
    is_alive = BRIDGE_HEALTH_MONITOR.check_status()
    app = AppSettings.load_static()
    status = "running" if is_alive else "stopped"

    col1, col2 = st.columns(2)
    col1.markdown(f"Monitoring Status: `{status}`")
    if col2.button("Edit"):
        edit_monitoring_settings(app)
    s_enabled = bool(app.monitor_slack_api_key)
    col1.markdown(f"Send slack notifications enabled: `{s_enabled}`.  To email `{app.monitor_slack_recipient_email}`")
    is_pagerduty_active = app.monitor_pager_duty_routing_key is not None
    col1.markdown(f"Send PagerDuty notifications enabled: `{is_pagerduty_active}`")
    col1.markdown(f"Check status every: `{app.monitor_check_interval_hours}` hours")
    p = ','.join(app.monitor_only_pools) if app.monitor_only_pools else "(all)"
    col1.markdown(f"Monitor selected pools: `{p}`")
    col1.markdown("---")

    if not is_alive:
        if st.button("Start Monitoring Agents"):
            with st.spinner("starting ..."):
                app.monitor_enable_monitoring = True
                app.save()
                BRIDGE_HEALTH_MONITOR.start(app)
                st.success("Monitoring Started")
                sleep(5)
                st.rerun()
    else:
        if st.button("Stop Monitoring"):
            with st.spinner("stopping ..."):
                app.monitor_enable_monitoring = False
                app.save()
                BRIDGE_HEALTH_MONITOR.stop()
                BRIDGE_HEALTH_MONITOR.last_message = ""
                BRIDGE_HEALTH_MONITOR.last_run = None
                st.warning("Monitoring Stopped")
                sleep(2)
                st.rerun()

    short_time_ago = f", `{StringUtils.short_time_ago(BRIDGE_HEALTH_MONITOR.last_run)}` ago" if BRIDGE_HEALTH_MONITOR.last_run else ""
    st.markdown(f"Last time run: `{BRIDGE_HEALTH_MONITOR.last_run}` {short_time_ago}")

    if BRIDGE_HEALTH_MONITOR.last_message:
        st.markdown("Last message:")
        cont = st.container(border=True)
        cont.text(f"{BRIDGE_HEALTH_MONITOR.last_message}")
        if BRIDGE_HEALTH_MONITOR.last_message_health == AgentHealthCategory.healthy:
            cont.success(f"All monitored agents Healthy")
        else:
            cont.warning("Some monitored agents Unhealthy")
    if st.button("🔄"):
        st.rerun()


PageUtil.set_page_config("Monitor Bridge Agent Health", "Monitor Bridge Agent Health", True)
page_content()

