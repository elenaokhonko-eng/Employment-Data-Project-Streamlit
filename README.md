# Singapore Jobs Opportunity Dashboard

Streamlit dashboard for the Module 1 Assignment Project: Singapore Jobs Analytics.

## Business Case

This dashboard helps career consultants and trainers identify Singapore job roles with stronger salary potential, healthy demand, and lower applicant competition. The target client is jobseekers who need practical guidance on which roles or training pathways may offer better opportunities.

## App Structure

The raw and cleaned datasets are too large for normal GitHub upload, so the deployed dashboard uses smaller summary files generated from the cleaned data.

```text
dashboard.py                 Streamlit app
clean_data.py                Cleans the raw CSV locally
create_clean_db.py           Optional DuckDB conversion script
create_dashboard_data.py     Creates dashboard-ready summary CSVs
data/                        Small summary files used by Streamlit
requirements.txt             Streamlit Cloud dependencies
```

Large local files are intentionally ignored:

```text
SGJobData.csv
SGJobData_cleaned.csv
SGJobData.db
SGJobData_cleaned.db
```

## Run Locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Generate dashboard summary data:

```bash
python create_dashboard_data.py
```

Run the app:

```bash
streamlit run dashboard.py
```

Open:

```text
http://localhost:8501
```

## Dashboard Views

- Overview: key metrics, top categories, and top job titles.
- Demand Trends: monthly posting trends and demand by category.
- Salary Analysis: median salary by category, seniority, and role.
- Competition: applications per posting and salary versus competition.
- Opportunity Finder: ranked shortlist of best-paid, lower-competition jobs.

## Performance Approach

The full cleaned data is processed locally into smaller dashboard-ready CSVs. Streamlit loads these files with `st.cache_data`, so the app avoids re-reading a large dataset on every sidebar filter change.
