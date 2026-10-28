from io import StringIO
import csv
import requests
import os
from datetime import datetime

# Download JSON directly from Reuters
url = "https://graphics.thomsonreuters.com/israel-election-results-2026/data.json"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0 Safari/537.36"
    )
}

response = requests.get(url, headers=headers)
response.raise_for_status()

data = response.json()
results = data["ElectionResults"]
timestamp = data["Timestamp"][0]["timestamp"]
total_votes = data["VotesCounted"][0]["total_votes"]
votes_counted = data["VotesCounted"][0]["votes_counted"]
votes_percentage = votes_counted/total_votes*100

# Parse timestamp
dt = datetime.strptime(timestamp, "%m/%d/%Y %H:%M:%S")

# String 1
footnote = (
    f"{votes_counted:,} votes counted of "
    f"{total_votes:,} total votes cast."
)

# String 2
intro = (
    f"{votes_percentage:.1f}% of votes counted, "
    f"as of {dt.strftime('%b. %-d, %-I:%M %p').replace('AM','a.m.').replace('PM','p.m.')} GMT"
)

print(vote_count_text)
print(status_text)

# Party order and display names for the CSV
blocs = {
    "Netanyahu-led bloc": [
        ("Likud", "Likud"),
        ("UTJ", "UTJ"),
        ("Jewish Power (Otzma Yehudit)", "Jewish Power"),
        ("SHAS", "SHAS"),
        ("Religious Zionism", "Religious Zionism"),
        ("People of Israel", "People of Israel"),
    ],
    "Opposition bloc": [
        ("Yashar", "Yashar"),
        ("Together (Beyachad)", "Together"),
        ("The Democrats", "The Democrats"),
        ("Israel Our Home (Yisrael Beiteinu)", "Israel Our Home"),
    ],
    "Unaligned parties": [
        ("The Joint List", "The Joint List"),
        ("Raam", "Ra’am"),
        ("The Reservists", "The Reservists"),
    ],
}

# Look up vote percentages by party
party_lookup = {
    row["party"]: float(row["percentage_votes"])
    for row in results
}

rows = ["who","percent"]

for bloc_name, parties in blocs.items():

    bloc_total = sum(
        party_lookup.get(source_name, 0)
        for source_name, display_name in parties
    )

    rows.append([
        f'<b>{bloc_name} <span style="font-size:20px;">{bloc_total:.2f}%</span></b>',
        ""
    ])

    for source_name, display_name in parties:
        rows.append([
            display_name,
            f'{party_lookup.get(source_name, 0):.2f}%'
        ])

    rows.append(["", ""])  # blank row

# CSV DATA
csv_buffer = StringIO()
csv.writer(csv_buffer).writerows(rows)
csv_data = csv_buffer.getvalue()

# FOR CHART UPDATE
API_TOKEN = os.environ["TOKEN"]
URL_BASE = os.environ["URL_BASE"]
CHART_ID = "J9CR1"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# UPDATE DATA
response = requests.put(
    f"{URL_BASE}charts/{CHART_ID}/data",
    headers=HEADERS,
    data=csv_data.encode("utf-8")
)

response.raise_for_status()

# UPDATE TITLE AND TIMESTAMP
payload = {
    "metadata": {
        "describe": {
            "intro": intro
        },
        "annotate": {
            "notes": footnote
        }
    }
}

response = requests.patch(
    f"{URL_BASE}charts/{CHART_ID}",
    json=payload,
    headers=HEADERS
)

response.raise_for_status()

# PUBLISH CHART
response = requests.post(
    f"{URL_BASE}charts/{CHART_ID}/publish",
    headers=HEADERS
)

response.raise_for_status()

print("Chart updated and published.")
