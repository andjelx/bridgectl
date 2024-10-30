import os

from src.cli.app_config import APP_CONFIG


class SharedUi:
    @staticmethod
    def show_app_version(cont, inc_dir: bool = False):
        cont.text("")
        cont.text("")
        cont.text("")
        cont2 = cont.columns(2)[0].container(border=True)
        if not inc_dir:
            cont2.text(f"version {APP_CONFIG.app_version}")
        cont2.text(f"downloaded from: {APP_CONFIG.target_github_repo}")
        if APP_CONFIG.is_devbuilds():
            cont2.text("internal devbuilds supported: True")
        if inc_dir:
            cont2.text(f"working directory: {os.getcwd()}")
        if not APP_CONFIG.is_devbuilds():
            cont2.markdown(
                """\n\n\n*Terms of Use*: This utility is community supported. Please get help from other users on the Tableau Community Forums. [License](https://github.com/tableau/bridgectl/blob/main/LICENSE.txt)""")
            cont2.markdown(
                "Please log any feature requests or issues on the github [issues](https://github.com/tableau/bridgectl/issues) tab.")
