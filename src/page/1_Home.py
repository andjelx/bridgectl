import streamlit as st
from PIL import Image

from src.page.ui_lib.page_util import PageUtil
from src.page.ui_lib.shared_ui import SharedUi
from src.cli.app_config import APP_CONFIG
from src.models import AppSettings


def page_content():
    if APP_CONFIG.is_devbuilds():
        from src.internal.devbuilds.devbuilds_const import DevBuildsLinks
        link = DevBuildsLinks.wiki_docs
    else:
        link = "https://github.com/tableau/bridgectl/blob/main/README.md"
    doc_link = f"[Documentation]({link})"
    st.markdown(f"**Build, run, and manage Tableau Bridge Containers.** {doc_link}")
    filename = "src/page/assets/tableau-bridge-2.png"
    image = Image.open(filename)
    st.write()
    st.write()
    st.image(image, width=170)
    cont = st.container()
    SharedUi.show_app_version(cont)
    # STEP - App Features
    app = AppSettings.load_static()
    cont_features = st.columns(2)[0].container(border=True)
    cont_features.subheader("Enabled Features for Tableau Bridge")
    show_feature("Build, run and monitor Bridge Linux Containers", True, cont_features)
    show_feature("AWS ECR Container Registry", app.feature_ecr_enabled, cont_features)
    show_feature("Kubernetes Integration", app.feature_k8s_enabled, cont_features)
    show_feature("Additional Pages (Example Scripts, Test Bridge, Jobs, Monitor)", app.feature_additional_pages_enabled, cont_features)
    if APP_CONFIG.is_devbuilds():
        cont_features.subheader("Enabled Features for Tableau Developers")
        show_feature("Hammerhead EC2 Instance Management", app.feature_hammerhead_enabled, cont_features)
    cont_features.html(f"<div style='text-align: center;'><span style='color:gray'><a href='/Settings?tab=features'>enable additional features</a></span></div>")


def show_feature(feature_name: str, is_enabled: bool, cont):
    if is_enabled:
        cont.html(f"<span style='font-size: 12px;'>✅</span>&nbsp; &nbsp; {feature_name}")
    else:
        cont.html(f"<span style='font-size: 12px;'>◻</span>️&nbsp; &nbsp; <span style='color:gray'>{feature_name}</span>")


PageUtil.set_page_config(page_title="Home", page_header="Tableau BridgeCTL")
page_content()

