import json
import pandas as pd
import numpy as np

RAW_FILE = "SGJobData.csv"
CLEAN_FILE = "SGJobData_cleaned.csv"

df = pd.read_csv(RAW_FILE)

print("Raw shape:", df.shape)
print(df.columns.tolist())

df = df[df["metadata_jobPostId"].notna()].copy()

print("After removing invalid rows:", df.shape)

date_cols = [
    "metadata_newPostingDate",
    "metadata_originalPostingDate",
    "metadata_expiryDate",
]

for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

df["posting_year"] = df["metadata_newPostingDate"].dt.year
df["posting_month"] = df["metadata_newPostingDate"].dt.to_period("M").astype(str)

text_cols = [
    "title",
    "postedCompany_name",
    "employmentTypes",
    "positionLevels",
    "salary_type",
    "status_jobStatus",
]

for col in text_cols:
    df[col] = (
        df[col]
        .astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
    )

df["title_clean"] = (
    df["title"]
    .str.lower()
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)

df["title_display"] = df["title_clean"].str.title()

num_cols = [
    "metadata_repostCount",
    "metadata_totalNumberJobApplication",
    "metadata_totalNumberOfView",
    "minimumYearsExperience",
    "numberOfVacancies",
    "salary_minimum",
    "salary_maximum",
    "average_salary",
]

for col in num_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df[df["salary_type"].eq("Monthly")].copy()

df = df[
    (df["average_salary"].notna())
    & (df["average_salary"] >= 1000)
    & (df["average_salary"] <= 30000)
].copy()

df["salary_band"] = pd.cut(
    df["average_salary"],
    bins=[0, 3000, 5000, 8000, 30000],
    labels=["<3000", "3000-4999", "5000-7999", "8000+"],
    include_lowest=True,
)

def extract_categories(value):
    try:
        categories = json.loads(value)
        return [item.get("category") for item in categories if item.get("category")]
    except Exception:
        return []

df["category_list"] = df["categories"].apply(extract_categories)
df["primary_category"] = df["category_list"].apply(lambda x: x[0] if x else "Unknown")

df["applications_per_posting"] = df["metadata_totalNumberJobApplication"].fillna(0)
df["views_per_posting"] = df["metadata_totalNumberOfView"].fillna(0)
df["vacancy_demand"] = df["numberOfVacancies"].fillna(1)

def seniority_group(row):
    level = str(row["positionLevels"]).lower()
    years = row["minimumYearsExperience"]

    if "fresh" in level or "entry" in level:
        return "Entry Level"
    if "junior" in level:
        return "Junior"
    if "senior management" in level or "senior" in level:
        return "Senior"
    if "manager" in level or "management" in level:
        return "Manager"
    if pd.notna(years):
        if years <= 1:
            return "Entry Level"
        if years <= 3:
            return "Junior"
        if years <= 7:
            return "Mid Level"
        return "Senior"

    return "Other"

df["seniority_group"] = df.apply(seniority_group, axis=1)

keywords = [
    "data",
    "analyst",
    "engineer",
    "manager",
    "sales",
    "admin",
    "python",
    "sql",
    "cloud",
    "finance",
    "marketing",
    "logistics",
]

for keyword in keywords:
    df[f"tag_{keyword}"] = df["title_clean"].str.contains(keyword, case=False, na=False)

df = df.drop(columns=["occupationId"], errors="ignore")

df.to_csv(CLEAN_FILE, index=False)

print("Cleaned shape:", df.shape)
print("Saved:", CLEAN_FILE)

print(df[[
    "title_clean",
    "primary_category",
    "employmentTypes",
    "positionLevels",
    "seniority_group",
    "average_salary",
    "salary_band",
    "applications_per_posting",
    "views_per_posting",
    "posting_month",
]].head())
