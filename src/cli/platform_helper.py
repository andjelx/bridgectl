import subprocess
import sys
import webbrowser

from src.cli.app_config import APP_NAME
from src.cli.app_logger import LOGGER
from src.models import CONFIG_DIR
from src.os_type import current_os, OsType
from src.subprocess_util import SubProcess


def not_supported_os():
    LOGGER.info(f"INVALID: local operating system '{current_os()}' not supported")


def open_webbrowser_util(url):
    if current_os() == OsType.mac:
        webbrowser.open(url)
    elif current_os() == OsType.win:
        webbrowser.open(url)
    else:
        not_supported_os()


# def edit_settings_in_text_editor():
#     try:
#         if not os.path.exists(token_file_path):
#             TokenLoader(LOGGER).create_example_token_file()
#
#         if current_os() == OsType.mac:
#             LOGGER.info(f"settings.yml path: {bridge_settings_file_util.config_file_full_path}")
#             LOGGER.info(f"tokens.yml path: {token_file_path}")
#             subprocess.run(['open', '-e', f'{token_file_path}'], check=True)
#             subprocess.run(['open', '-e', f'{bridge_settings_file_util.config_file_full_path}'], check=True)
#         elif current_os() == OsType.win:
#             webbrowser.open(bridge_settings_file_util.config_file_full_path)
#             webbrowser.open(token_file_path)
#         elif current_os() == OsType.linux:
#             config_str = bridge_settings_file_util.load_settings_as_string()
#             LOGGER.info(f"settings.yml contents:\n======\n{config_str}======")
#             tokens_str =  TokenLoader(LOGGER).display_tokens()
#             LOGGER.info(f"tokens.yml contents:\n======\n{tokens_str}======")
#             LOGGER.info("command to edit:")
#             LOGGER.info(f"vi {bridge_settings_file_util.config_file_full_path}")
#             LOGGER.info(f"vi {token_file_path}")
#         else:
#             not_supported_os()
#         LOGGER.info()
#     except Exception as ex:
#         LOGGER.error(f"unable to open settings in text editor. error: ", ex=ex)


def view_app_logs():
    LOGGER.info(f"reveal {APP_NAME} logs in finder\n path: {CONFIG_DIR}")
    if current_os() == OsType.mac:
        subprocess.run(['open', '-R', f'{CONFIG_DIR}'], check=True)
    elif current_os() == OsType.win:
        webbrowser.open(CONFIG_DIR)
    else:
        not_supported_os()
    #FutureDev: remove listing of pip modules.
    LOGGER.info("List of pip modules installed: ")
    cmds = [f'{sys.executable} -m pip list']
    SubProcess(LOGGER).run_cmd(cmds, display_output=True)



