# National Broadband Tool 🛰️
**Identifying underserved US communities for broadband investment — UChicago MS capstone with US Ignite (Best Capstone Award, 2023)**

The National Broadband Tool helps policymakers and funders decide *where* to invest in connectivity. It combines census and broadband-access data with clustering and prediction models to rank US cities by need, and presents the results in an interactive map so a non-technical user can go from "the whole country" to "this specific place" in two clicks.

Built for [US Ignite](https://www.us-ignite.org/) as the University of Chicago Applied Data Science capstone (team of 4; I was team lead). US Ignite owns the production IP; this repo is the public-facing dashboard and modelling approach.

## What it does
- **National view** — choropleth map of all 50 states, DC, and Puerto Rico colored by a Digital Index (share of connections above 25 Mbps). Dark red = priority zones.
- **State drill-down** — select a state to see city- and county-level detail and the model's ranked candidates.
- **Underserved-city identification** — DBSCAN clustering on growth patterns plus an XGBoost model trained on census and connectivity features to surface cities most likely to benefit from investment.
- **Proposal drafting (capstone deliverable)** — a custom OpenAI chatbot that produced first-draft funding proposals from public sources for a selected community.

## Stack
Python · pandas · GeoPandas · scikit-learn · XGBoost · Folium · Streamlit · Parquet

## Data
US Census (ACS) demographic and economic features; FCC / public broadband-connection data at state and city level (2021). Processed data lives in `DATA/`; trained models in `MODELS/`.

## Run it
    pip install -r requirements.txt
    streamlit run app.py

## Team
Shweta Sampath Kumar, Swathi Ganesan, Marc Edwards, Kishor Mannur Reddy — University of Chicago, MS Applied Data Science, 2023.
Mentors: Don Pitchell, US Ignite stakeholders.
