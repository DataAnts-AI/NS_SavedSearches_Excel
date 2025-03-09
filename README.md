# NetSuite-Streamlit Integration

## Overview
This repository integrates NetSuite ERP saved searches with a Streamlit web application using a NetSuite RESTlet.

<img width="671" alt="image" src="https://github.com/user-attachments/assets/49609bb3-0aa6-4f65-94d3-bc4d2adc1635" />


## Repository Structure
```
├── restlet_savedsearch_final.js  # NetSuite RESTlet script
├── ns_ss_refresh.py             # Streamlit app to manage Excel exports
```

## Requirements

### NetSuite
- Account with active RESTlet deployment

### Streamlit and Python dependencies:
- Streamlit
- pandas
- openpyxl
- requests
- requests_oauthlib

Install dependencies:
```bash
pip install streamlit pandas openpyxl requests requests_oauthlib
```

## Configuration
Create a `.streamlit/secrets.toml` file with your NetSuite credentials:

```toml
NS_ACCOUNT_ID = "your_account_id"
NS_CONSUMER_KEY = "your_consumer_key"
NS_CONSUMER_SECRET = "your_consumer_secret"
NS_TOKEN_ID = "your_token_id"
NS_TOKEN_SECRET = "your_token_secret"
NS_RESTLET_URL = "your_restlet_url"
NS_SCRIPT_ID = "your_script_id"
NS_DEPLOY_ID = "your_deploy_id"
```

## Deployment in NetSuite
- Navigate to **Customization → Scripting → Scripts → New**
- Upload `restlet_savedsearch_final.js`
- Deploy as a RESTlet, set status to **Released**, and record script and deploy IDs

## Usage

### Choose Operation
A radio button allows users to select between:
- **Export New Excel File**
- **Refresh Existing Excel File**

### Export New Excel File
1. The app retrieves saved searches from NetSuite.
2. Users select which searches to include.
3. Data is fetched via RESTlet and saved into individual Excel sheets.
4. Users can download the new Excel file.

### Refresh Existing Excel File
1. Users upload an existing Excel file.
2. Users select searches to refresh.
3. The app fetches updated data from NetSuite and updates the Excel sheets.
4. Users can download the refreshed Excel file.

## Auto-Refresh
Supports periodic auto-refresh functionality to maintain updated data without manual intervention.

## Support
For assistance or reporting issues, please open an issue on GitHub.
