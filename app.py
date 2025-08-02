import pandas as pd
from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HTML_TEMPLATE = """ ... (same as your original HTML) ... """  # use full HTML as-is

BASE_URL = 'https://nikhilraghav.site/vehicleapinikhilapiapi/'

def get_file_urls_from_webpage(url):
    urls = []
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].endswith('.csv'): 
                urls.append(requests.compat.urljoin(url, link['href']))
        return urls
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return []

dataframes = []
file_urls = get_file_urls_from_webpage(BASE_URL)

if file_urls:
    for url in sorted(file_urls):
        try:
            df_part = pd.read_csv(url, low_memory=False)
            if 'Registration No.' in df_part.columns:
                df_part.rename(columns={'Registration No.': 'regno'}, inplace=True)
            elif 'Reg No' in df_part.columns:
                df_part.rename(columns={'Reg No': 'regno'}, inplace=True)
            dataframes.append(df_part)
        except Exception as e:
            print(f"Error loading {url}: {e}")

if dataframes:
    df_combined = pd.concat(dataframes, ignore_index=True).fillna('N/A')
    if 'regno' in df_combined.columns:
        df_combined['regno'] = df_combined['regno'].astype(str)
else:
    df_combined = pd.DataFrame()

def find_vehicle_by_regno(regno):
    if df_combined.empty or not regno:
        return None
    matches = df_combined[df_combined['regno'].str.upper() == regno.upper()]
    if matches.empty:
        return None
    return matches.iloc[0].to_dict()

@app.route("/")
def index():
    return """
    <h1>Vehicle API is Running</h1>
    <p>Use the following endpoints:</p>
    <ul>
        <li><code>/search?regno=YOUR_REGNO</code> - To get raw JSON data.</li>
        <li><code>/view?regno=YOUR_REGNO</code> - To get a clean HTML view.</li>
    </ul>
    """

@app.route("/search")
def search_json():
    regno = request.args.get("regno")
    vehicle_details = find_vehicle_by_regno(regno)
    if vehicle_details:
        return jsonify(vehicle_details)
    else:
        return jsonify({"error": f"No data found for registration number: {regno}"}), 404

@app.route("/view")
def search_html():
    regno = request.args.get("regno")
    vehicle_details = find_vehicle_by_regno(regno)
    return render_template_string(HTML_TEMPLATE, details=vehicle_details)
