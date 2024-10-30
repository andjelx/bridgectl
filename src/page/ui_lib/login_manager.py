from time import sleep

import streamlit as st

from src.models import AppSettings


class LoginManager:
    @staticmethod
    def check_login(app: AppSettings):
        if not app.login_password_for_bridgectl: # no password is set up.
            return True

        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False

        if st.session_state['logged_in']:
            return True
        else:
            st.title("BridgeCTL Login")
            with st.form(key='login_form'):
                pwd = st.text_input("Enter password", type="password", help="This password can be changed by editing `config/app_settings.yml`. To remove the login password, set it to blank.")
                if st.form_submit_button(label='Login'):
                    if pwd == app.login_password_for_bridgectl:
                        st.session_state['logged_in'] = True
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Incorrect password. Please try again.")
            return False

    @staticmethod
    def update_login(app: AppSettings, cont):
        cont.subheader("Configure Login Password")
        if app.login_password_for_bridgectl:
            if cont.button("Logout"):
                st.session_state['logged_in'] = False
                st.rerun()
        else:
            cont.html(f"<span style='color:gray'>No login password configured</span?")
        with cont.expander("Change password"):
            with st.form(key='login_form', border=False):
                pwd = st.text_input("Set password", type="password")
                if st.form_submit_button("Save"):
                    st.session_state['logged_in'] = False
                    app.login_password_for_bridgectl = pwd
                    app.save()
                    st.success("saved")
                    sleep(.7)
                    st.rerun()