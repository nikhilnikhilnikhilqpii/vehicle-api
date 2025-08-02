import pandas as pd
from flask import Flask, request, jsonify, render_template_string
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- HTML Template for a clean view ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vehicle Details: {{ details.get('regno', 'Not Found') }}</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 0; background-color: #f8f9fa; }
        .container { padding: 20px; max-width: 800px; margin: 20px auto; background: #ffffff; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px; }
        h1 { color: #343a40; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: 12px; border-bottom: 1px solid #dee2e6; word-break: break-all; }
        th { background-color: #4CAF50; color: white; width: 30%; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .error { color: #dc3545; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vehicle Details</h1>
        {% if details %}
            <table>
                {% for key, value in details.items() %}
                <tr>
                    <th>{{ key.replace('_', ' ').title() }}</th>
                    <td>{{ value if value not in [None, 'NaN', 'nan'] else 'N/A' }}</td>
                </tr>
                {% endfor %}
            </table>
        {% else %}
            <p class="error">No details found for the given registration number.</p>
        {% endif %}
    </div>
</body>
</html>
"""

# --- Data Loading Section (Pehle jaisa hi hai) ---
BASE_URL = 'https://nikhilraghav.site/vehicleapinikhilapiapi/'

def get_file_urls_from_webpage(url):
    urls = []
    try:
        print(f"Fetching file list from: {url}")
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].endswith('.csv'): 
                urls.append(requests.compat.urljoin(url, link['href']))
        print(f"✅ Found {len(urls)} .csv files.")
        return urls
    except Exception as e:
        print(f"❌ Error fetching URL: {e}")
        return []

dataframes = []
file_urls = get_file_urls_from_webpage(BASE_URL)

if file_urls:
    for url in sorted(file_urls):
        try:
            print(f"🔄 Loading: {url.split('/')[-1]}")
            df_part = pd.read_csv(url, low_memory=False)
            if 'Registration No.' in df_part.columns:
                df_part.rename(columns={'Registration No.': 'regno'}, inplace=True)
            elif 'Reg No' in df_part.columns:
                df_part.rename(columns={'Reg No': 'regno'}, inplace=True)
            dataframes.append(df_part)
        except Exception as e:
            print(f"⚠️ Error loading data from {url}: {e}")

if dataframes:
    df_combined = pd.concat(dataframes, ignore_index=True).fillna('N/A')
    if 'regno' in df_combined.columns:
        df_combined['regno'] = df_combined['regno'].astype(str)
    print(f"🚀 All data combined! Total Rows: {len(df_combined)}")
else:
    df_combined = pd.DataFrame()


# --- Search Function (Dono endpoints use karenge) ---
def find_vehicle_by_regno(regno):
    if df_combined.empty or not regno:
        return None
    matches = df_combined[df_combined['regno'].str.upper() == regno.upper()]
    if matches.empty:
        return None
    # Pehla match uthao aur dictionary mein convert karo
    return matches.iloc[0].to_dict()


# --- API Endpoints Section ---
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
