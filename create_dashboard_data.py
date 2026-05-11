from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_FILE = PROJECT_DIR / "SGJobData_cleaned.csv"
DATA_DIR = PROJECT_DIR / "data"


def minmax(series: pd.Series) -> pd.Series:
    series = series.astype(float)
    low = series.min()
    high = series.max()
    if pd.isna(low) or pd.isna(high) or high == low:
        return pd.Series(0.5, index=series.index)
    return (series - low) / (high - low)


def add_opportunity_score(df: pd.DataFrame) -> pd.DataFrame:
    scored = df.copy()
    scored["salary_score"] = minmax(scored["median_salary"])
    scored["demand_score"] = minmax(np.log1p(scored["postings"]))
    scored["vacancy_score"] = minmax(np.log1p(scored["total_vacancies"]))
    scored["competition_score"] = 1 - minmax(np.log1p(scored["avg_applications"]))
    scored["opportunity_score"] = (
        0.40 * scored["salary_score"]
        + 0.25 * scored["demand_score"]
        + 0.15 * scored["vacancy_score"]
        + 0.20 * scored["competition_score"]
    ) * 100
    scored["opportunity_score"] = scored["opportunity_score"].round(1)
    return scored


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing cleaned source file: {SOURCE_FILE}")

    DATA_DIR.mkdir(exist_ok=True)
    print(f"Loading cleaned data: {SOURCE_FILE.name}")

    usecols = [
        "metadata_jobPostId",
        "metadata_newPostingDate",
        "posting_month",
        "employmentTypes",
        "positionLevels",
        "seniority_group",
        "postedCompany_name",
        "title_clean",
        "title_display",
        "salary_band",
        "primary_category",
        "average_salary",
        "numberOfVacancies",
        "applications_per_posting",
        "views_per_posting",
        "vacancy_demand",
        "tag_data",
        "tag_analyst",
        "tag_engineer",
        "tag_manager",
        "tag_sales",
        "tag_admin",
        "tag_python",
        "tag_sql",
        "tag_cloud",
        "tag_finance",
        "tag_marketing",
        "tag_logistics",
    ]

    df = pd.read_csv(SOURCE_FILE, usecols=usecols)
    df["metadata_newPostingDate"] = pd.to_datetime(df["metadata_newPostingDate"], errors="coerce")
    df["posting_month"] = pd.to_datetime(df["posting_month"], errors="coerce")
    df["primary_category"] = df["primary_category"].fillna("Unknown")
    df["seniority_group"] = df["seniority_group"].fillna("Other")
    df["salary_band"] = df["salary_band"].fillna("Unknown")
    df["vacancy_demand"] = df["vacancy_demand"].fillna(1)
    df["applications_per_posting"] = df["applications_per_posting"].fillna(0)
    df["views_per_posting"] = df["views_per_posting"].fillna(0)

    overview = pd.DataFrame(
        [
            {
                "total_postings": len(df),
                "total_vacancies": int(df["vacancy_demand"].sum()),
                "median_salary": round(float(df["average_salary"].median()), 2),
                "avg_applications": round(float(df["applications_per_posting"].mean()), 2),
                "avg_views": round(float(df["views_per_posting"].mean()), 2),
                "category_count": int(df["primary_category"].nunique()),
                "month_min": df["posting_month"].min().strftime("%Y-%m"),
                "month_max": df["posting_month"].max().strftime("%Y-%m"),
            }
        ]
    )
    overview.to_csv(DATA_DIR / "overview_metrics.csv", index=False)

    category_summary = (
        df.groupby("primary_category", as_index=False)
        .agg(
            postings=("metadata_jobPostId", "count"),
            total_vacancies=("vacancy_demand", "sum"),
            median_salary=("average_salary", "median"),
            avg_applications=("applications_per_posting", "mean"),
            avg_views=("views_per_posting", "mean"),
        )
        .query("postings >= 50")
    )
    category_summary = add_opportunity_score(category_summary)
    category_summary.to_csv(DATA_DIR / "category_summary.csv", index=False)

    title_summary = (
        df.groupby(["title_clean", "title_display", "primary_category"], as_index=False)
        .agg(
            postings=("metadata_jobPostId", "count"),
            total_vacancies=("vacancy_demand", "sum"),
            median_salary=("average_salary", "median"),
            avg_applications=("applications_per_posting", "mean"),
            avg_views=("views_per_posting", "mean"),
        )
        .query("postings >= 20")
    )
    title_summary = add_opportunity_score(title_summary)
    title_summary.to_csv(DATA_DIR / "title_summary.csv", index=False)

    monthly_trends = (
        df.groupby(["posting_month", "primary_category"], as_index=False)
        .agg(
            postings=("metadata_jobPostId", "count"),
            total_vacancies=("vacancy_demand", "sum"),
            median_salary=("average_salary", "median"),
            avg_applications=("applications_per_posting", "mean"),
        )
    )
    monthly_trends["posting_month"] = monthly_trends["posting_month"].dt.strftime("%Y-%m")
    monthly_trends.to_csv(DATA_DIR / "monthly_trends.csv", index=False)

    salary_summary = (
        df.groupby(["primary_category", "seniority_group", "salary_band"], as_index=False, observed=True)
        .agg(
            postings=("metadata_jobPostId", "count"),
            median_salary=("average_salary", "median"),
            avg_applications=("applications_per_posting", "mean"),
        )
        .query("postings >= 20")
    )
    salary_summary.to_csv(DATA_DIR / "salary_summary.csv", index=False)

    competition_summary = title_summary[
        [
            "title_display",
            "primary_category",
            "postings",
            "median_salary",
            "avg_applications",
            "avg_views",
            "opportunity_score",
        ]
    ].copy()
    competition_summary["competition_level"] = pd.cut(
        competition_summary["avg_applications"],
        bins=[-0.01, 1, 5, np.inf],
        labels=["Low", "Medium", "High"],
    )
    competition_summary.to_csv(DATA_DIR / "competition_summary.csv", index=False)

    sample_jobs = df[
        [
            "metadata_jobPostId",
            "metadata_newPostingDate",
            "title_display",
            "primary_category",
            "employmentTypes",
            "seniority_group",
            "salary_band",
            "average_salary",
            "applications_per_posting",
            "views_per_posting",
            "vacancy_demand",
        ]
    ].sample(n=min(15000, len(df)), random_state=42)
    sample_jobs["metadata_newPostingDate"] = sample_jobs["metadata_newPostingDate"].dt.strftime("%Y-%m-%d")
    sample_jobs.to_csv(DATA_DIR / "sample_jobs.csv", index=False)

    print("Dashboard data files created:")
    for file_path in sorted(DATA_DIR.glob("*.csv")):
        print(f"  {file_path.name}: {file_path.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
