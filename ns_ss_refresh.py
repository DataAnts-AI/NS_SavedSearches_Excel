import streamlit as st
import requests
from requests_oauthlib import OAuth1
import pandas as pd
from io import BytesIO
import urllib.parse
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

# ========== NETSUITE CONFIG ==========
NS_CONFIG = {
    "account_id": st.secrets["NS_ACCOUNT_ID"],
    "consumer_key": st.secrets["NS_CONSUMER_KEY"],
    "consumer_secret": st.secrets["NS_CONSUMER_SECRET"],
    "token_id": st.secrets["NS_TOKEN_ID"],
    "token_secret": st.secrets["NS_TOKEN_SECRET"],
    "restlet_url": st.secrets["NS_RESTLET_URL"],  # e.g. "https://<account_id>-sb1.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
    "script_id": st.secrets["NS_SCRIPT_ID"],       # e.g. "customscript_restlet_saved_search"
    "deploy_id": st.secrets["NS_DEPLOY_ID"]        # e.g. "customdeploy_restlet_saved_search"
}

class NetSuiteClient:
    def __init__(self, config):
        self.config = config
        self.auth = OAuth1(
            client_key=config["consumer_key"],
            client_secret=config["consumer_secret"],
            resource_owner_key=config["token_id"],
            resource_owner_secret=config["token_secret"],
            realm=config["account_id"],
            signature_method='HMAC-SHA256'
        )
        self.base_params = {
            "script": config["script_id"],
            "deploy": config["deploy_id"]
        }

    def _make_request(self, params):
        """Universal request handler with debugging."""
        all_params = {**self.base_params, **params}
        query_string = urllib.parse.urlencode(all_params, doseq=True)
        full_url = f"{self.config['restlet_url']}?{query_string}"
        #st.write(f"🔧 Debug URL: `{full_url}`")
        try:
            response = requests.get(
                self.config["restlet_url"],
                auth=self.auth,
                params=all_params,
                timeout=10
            )
            return response
        except Exception as e:
            st.error(f"Request failed: {str(e)}")
            return None

    def get_saved_searches(self):
        """Retrieve the list of saved searches from NetSuite."""
        response = self._make_request({"action": "list"})
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get("success"):
                    return data["searches"]
                else:
                    st.error(f"Error from RESTlet: {data.get('error')}")
            except Exception as e:
                st.error(f"JSON Error: {str(e)}")
        return []

    def fetch_data(self, search_names):
        """Fetch saved search data for the given list of search names."""
        if not search_names:
            return {}
        names_str = ",".join(search_names)
        response = self._make_request({"searchNames": names_str})
        if response and response.status_code == 200:
            try:
                data = response.json()
                if data.get("success"):
                    return data.get("results", {})
                else:
                    st.error(f"Error from RESTlet: {data.get('error')}")
            except Exception as e:
                st.error(f"JSON Error: {str(e)}")
        return {}

def export_new_excel(ns_client):
    st.subheader("Export New Excel File")
    searches = ns_client.get_saved_searches()
    if not searches:
        st.error("No saved searches found.")
        return
    # Build a mapping for display.
    search_options = {f"{s['name']} ({s['type']})": s for s in searches}
    selected = st.multiselect("Select Saved Searches:", list(search_options.keys()))
    if st.button("Export New Excel File"):
        if not selected:
            st.error("Select at least one saved search!")
            return
        selected_searches = [search_options[s] for s in selected]
        search_names = [s["name"] for s in selected_searches]
        with st.spinner("Fetching data from NetSuite..."):
            data = ns_client.fetch_data(search_names)
        if not data:
            st.error("No data returned from NetSuite!")
            return
        # Write the data to a new Excel file.
        with BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for search_name, rows in data.items():
                    df = pd.DataFrame(rows)
                    sheet_name = search_name[:31]  # Excel sheet name limit
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            st.success("Excel file created!")
            st.download_button(
                label="Download New Excel File",
                data=buffer.getvalue(),
                file_name="netsuite_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def refresh_existing_excel(ns_client):
    st.subheader("Refresh Existing Excel File")
    searches = ns_client.get_saved_searches()
    if not searches:
        st.error("No saved searches found.")
        return
    # Mapping for display.
    search_options = {f"{s['name']} ({s['type']})": s for s in searches}
    selected = st.multiselect("Select Saved Searches to Refresh:", list(search_options.keys()))
    excel_file = st.file_uploader("Upload Existing Excel File:", type=["xlsx"])
    
    # Option to auto refresh every 1 hour.
    auto_refresh_enabled = st.checkbox("Enable Auto Refresh (Every 1 Hour)")
    if auto_refresh_enabled:
        # This will cause the app to re-run every 3600000 ms (1 hour)
        st_autorefresh(interval=360000, key="auto_refresh")
    
    if st.button("Refresh Excel File"):
        if not selected:
            st.error("Select at least one saved search!")
            return
        if not excel_file:
            st.error("Please upload an existing Excel file!")
            return
        selected_searches = [search_options[s] for s in selected]
        search_names = [s["name"] for s in selected_searches]
        with st.spinner("Fetching updated data from NetSuite..."):
            data = ns_client.fetch_data(search_names)
        if not data:
            st.error("No data returned from NetSuite!")
            return
        try:
            existing_sheets = pd.read_excel(excel_file, sheet_name=None)
        except Exception as e:
            st.error(f"Error reading the uploaded Excel file: {e}")
            return
        # Merge existing sheets with updated data.
        all_sheets = existing_sheets.copy()
        for search_name in search_names:
            new_sheet = search_name[:31]
            new_data = pd.DataFrame(data.get(search_name, []))
            all_sheets[new_sheet] = new_data
        with BytesIO() as buffer:
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for sheet_name, df in all_sheets.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            st.success("Excel file refreshed!")
            st.download_button(
                label="Download Refreshed Excel File",
                data=buffer.getvalue(),
                file_name="refreshed_netsuite_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def main():
    st.title("NetSuite Saved Search Excel Updater")
    ns_client = NetSuiteClient(NS_CONFIG)
    st.markdown("""
    This app allows you to export a new Excel file with NetSuite saved search data **or**
    refresh an existing Excel file with updated data.  
    You can also enable auto refresh to update the file every hour.
    """)
    mode = st.radio("Choose Operation", options=["Export New Excel File", "Refresh Existing Excel File"])
    if mode == "Export New Excel File":
        export_new_excel(ns_client)
    elif mode == "Refresh Existing Excel File":
        refresh_existing_excel(ns_client)

if __name__ == "__main__":
    main()
