from fastapi import FastAPI
from fastapi.responses import HTMLResponse

import pandas as pd

# -------------------------------------------------
# Create FastAPI app
# -------------------------------------------------
app = FastAPI()

# -------------------------------------------------
# Health check endpoint
# -------------------------------------------------
@app.get("/health")
def health_check():
    return {"message": "Skin Clinic Campaign API is running"}

# -------------------------------------------------
# Campaign analysis function
# -------------------------------------------------
def generate_campaign_summary():

    df = pd.read_csv("skin_clinic_campaign.csv")

    # Convert response to 1/0 so the mean gives the response rate
    df["Response_to_Campaign"] = df["Response_to_Campaign"].map({"Yes": 1, "No": 0})

    # Product usage bands: 1-4, 5-8, >8
    df["Product_Group"] = pd.cut(
        df["Unique_Products_Purchased"],
        bins=[0, 4, 8, float("inf")],
        labels=["1-4", "5-8", ">8"]
    )

    # 1. Gender vs Campaign Response
    gender_df = df.groupby("Gender")["Response_to_Campaign"].mean() * 100
    gender_df = gender_df.round(2).reset_index()
    gender_df.columns = ["Gender", "Response_Rate_%"]

    # 2. Age Group vs Campaign Response
    age_df = df.groupby("AgeGroup")["Response_to_Campaign"].mean() * 100
    age_df = age_df.reindex(["<30", "30-50", ">50"]).round(2).reset_index()
    age_df.columns = ["Age_Group", "Response_Rate_%"]

    # 3. Purchase in Last Quarter vs Campaign Response
    purchase_df = df.groupby("Purchase_Last_Quarter")["Response_to_Campaign"].mean() * 100
    purchase_df = purchase_df.reindex(["Yes", "No"]).round(2).reset_index()
    purchase_df.columns = ["Purchase_Last_Quarter", "Response_Rate_%"]

    # 4. Product Usage vs Campaign Response
    product_df = df.groupby("Product_Group", observed=False)["Response_to_Campaign"].mean() * 100
    product_df = product_df.round(2).reset_index()
    product_df["Product_Group"] = product_df["Product_Group"].astype(str)
    product_df.columns = ["Products_Purchased", "Response_Rate_%"]

    return {
        "gender": gender_df,
        "age_group": age_df,
        "purchase_last_quarter": purchase_df,
        "product_usage": product_df
    }


# -------------------------------------------------
# API endpoint returning JSON data
# -------------------------------------------------
@app.get("/campaign-data")
def get_campaign_data():
    tables = generate_campaign_summary()
    return {name: table.to_dict(orient="records") for name, table in tables.items()}


# -------------------------------------------------
# Endpoint displaying results in tabular format
# -------------------------------------------------
@app.get("/campaign-analysis", response_class=HTMLResponse)
def campaign_analysis():

    tables = generate_campaign_summary()

    titles = {
        "gender": "1. Gender vs Campaign Response",
        "age_group": "2. Age Group vs Campaign Response",
        "purchase_last_quarter": "3. Purchase in Last Quarter vs Campaign Response",
        "product_usage": "4. Product Usage vs Campaign Response"
    }

    tables_html = ""
    for name, table in tables.items():
        tables_html += f"<h3>{titles[name]}</h3>"
        tables_html += table.to_html(index=False)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Skin Clinic Campaign Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
            }}
            table {{
                border-collapse: collapse;
                width: 50%;
                margin-bottom: 30px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 8px;
                text-align: center;
            }}
            th {{
                background-color: #f4f4f4;
            }}
        </style>
    </head>
    <body>

        <h2>Skin Clinic Campaign Analysis</h2>

        {tables_html}

    </body>
    </html>
    """

    return html_content


# -------------------------------------------------
# Home page
# -------------------------------------------------
@app.get("/")
def home():
    return {"message": "Go to /campaign-analysis to see the results"}
