import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep

from src.page.ui_lib.page_util import PageUtil
from src.cli import bridge_status_logic
from src.cli.app_config import APP_NAME
from src.lib.pagerduty_client import PagerDutyClient
from src.lib.slack_util import SlackUtil
from src.models import AppSettings
from src.monitor.background_task import BackgroundTask, BG_LOGGER


@dataclass
class AgentReport:
    agent_name: str = None
    pool_name: str = None
    status: str = None

class AgentHealthCategory:
    healthy = "healthy"
    unhealthy = "unhealthy"

class BridgeHealthMonitor:
    def __init__(self):
        self.slack_client = None
        self.pager_duty_client = None
        self.bg_task = BackgroundTask(self.check_agents_loop)
        self.slack_email = None
        self.run_interval = None
        self.monitor_only_pools = None
        self.monitor_only_pools_display = None
        self.last_run = None
        self.last_message = ""
        self.last_message_health = None

    def change_settings(self, app: AppSettings):
        self.slack_email = app.monitor_slack_recipient_email
        self.run_interval = timedelta(hours=app.monitor_check_interval_hours)
        self.monitor_only_pools = app.monitor_only_pools if app.monitor_only_pools else []
        self.monitor_only_pools_display = ', '.join(self.monitor_only_pools) if self.monitor_only_pools else "(all)"
        if app.monitor_slack_api_key:
            self.slack_client = SlackUtil(BG_LOGGER, app.monitor_slack_api_key)
        if app.monitor_pager_duty_routing_key:
            self.pager_duty_client = PagerDutyClient(app.monitor_pager_duty_routing_key)

    def check_status(self):
        return self.bg_task.check_status()

    def start(self, app: AppSettings):
        self.change_settings(app)
        BG_LOGGER.info("starting background task to monitor bridge agent connection")
        self.last_run = None
        return self.bg_task.start()

    def stop(self):
        return self.bg_task.stop()

    def trigger_run_now(self):
        self.last_run = None
        self.last_message = ""

    def display_interval(self):
        seconds = self.run_interval.total_seconds()
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

    def check_agents_loop(self):
        while not self.bg_task.stop_event.is_set():
            sleep(.1)
            if not self.last_run or (datetime.now(timezone.utc) - self.last_run >= self.run_interval):
                self.last_run = datetime.now(timezone.utc)
                self.do_check_agents()
                sleep(3)
        BG_LOGGER.info("Background task check_agents has stopped.")

    def log_msg(self, msg):
        BG_LOGGER.info(msg)
        self.last_message += "\n" + msg

    def do_check_agents(self):
        try:
            token = PageUtil.get_admin_pat_or_log_error(BG_LOGGER)
            if not token:
                return
            BG_LOGGER.info(f"checking health of bridge agents")
            agents_status, headers = bridge_status_logic.display_bridge_status(token, BG_LOGGER, True)
            self.last_message = ""
            self.last_message_health = None
            agents_monitored = []
            agents_disconnected = []
            agents_by_pool_count = {}
            if self.monitor_only_pools:
                agents_by_pool_count = dict.fromkeys(self.monitor_only_pools, 0)
            for a in agents_status:
                ar = AgentReport(agent_name=a[0], pool_name=a[1], status=a[4])
                if ar.pool_name in agents_by_pool_count:
                    agents_by_pool_count[ar.pool_name] += 1
                ar.pool_name = a[1]
                if self.monitor_only_pools and ar.pool_name not in self.monitor_only_pools:
                    continue
                agents_monitored.append(ar)
                if ar.status != "CONNECTED":
                    agents_disconnected.append(ar)
            # check if any of the values in agents_by_pool_count are 0
            msg_empty_pool = ""
            if self.monitor_only_pools and 0 in agents_by_pool_count.values():
                for pool_name in agents_by_pool_count:
                    if agents_by_pool_count[pool_name] == 0:
                        msg_empty_pool += f" no agents in pool `{pool_name}`."
            if len(agents_disconnected) == 0 and not msg_empty_pool:
                self.last_message_health = AgentHealthCategory.healthy
                mh = f"all monitored agents healthy in pool {self.monitor_only_pools_display} for site {token.sitename}"
                self.log_msg(mh)
            else:
                self.last_message_health = AgentHealthCategory.unhealthy
                msg = ""
                if msg_empty_pool:
                    msg += f"{APP_NAME} detected empty pool for Tableau Cloud site *{token.sitename}*\n"
                    msg += msg_empty_pool
                if len(agents_disconnected) > 0:
                    msg = f"{APP_NAME} detected unhealthy Tableau Bridge Agents for Tableau Cloud site *{token.sitename}*\n"
                    msg += f"unhealthy agents: {len(agents_disconnected)} of {len(agents_monitored)} in pool: {self.monitor_only_pools_display}\n"
                    msg += "\n".join(f'    {a.agent_name} {a.status}, pool: {a.pool_name}' for a in agents_disconnected)
                self.log_msg(msg)
                if self.pager_duty_client:
                    self.pager_duty_client.trigger_pagerduty_alert("Tableau Cloud Bridge Agents Disconnected", msg)
                    self.log_msg("PagerDuty alert triggered")
                if not self.slack_client or not self.slack_email:
                    self.log_msg("Slack api key or email are not set")
                else:
                    self.slack_client.send_private_message(self.slack_email, msg)
                    self.log_msg("Slack alert sent")
            self.last_run = datetime.now(timezone.utc)
        except Exception as ex:
            stack_trace = traceback.format_exc()
            msg = f"Error in check_agents:\n{stack_trace}"
            BG_LOGGER.error(msg)
            self.last_message += msg

BRIDGE_HEALTH_MONITOR = BridgeHealthMonitor()