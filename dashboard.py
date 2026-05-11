from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="Singapore Jobs Opportunity Dashboard", layout="wide")

DATA_DIR = Path(__file__).resolve().parent / "data"


@st.cache_data(show_spinner="Loading dashboard data...")
def load_dashboard_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    data = {
        "overview": pd.read_csv(data_dir / "overview_metrics.csv"),
        "category": pd.read_csv(data_dir / "category_summary.csv"),
        "title": pd.read_csv(data_dir / "title_summary.csv"),
        "monthly": pd.read_csv(data_dir / "monthly_trends.csv"),
        "salary": pd.read_csv(data_dir / "salary_summary.csv"),
        "competition": pd.read_csv(data_dir / "competition_summary.csv"),
        "sample": pd.read_csv(data_dir / "sample_jobs.csv"),
    }
    data["monthly"]["posting_month"] = pd.to_datetime(data["monthly"]["posting_month"])
    return data


def filter_categories(df: pd.DataFrame, selected_categories: list[str]) -> pd.DataFrame:
    if selected_categories and "primary_category" in df.columns:
        return df[df["primary_category"].isin(selected_categories)]
    return df


if not DATA_DIR.exists():
    st.error("Dashboard data folder was not found. Run create_dashboard_data.py first.")
    st.stop()

data = load_dashboard_data(DATA_DIR)
overview = data["overview"].iloc[0]
category_df = data["category"]
title_df = data["title"]
monthly_df = data["monthly"]
salary_df = data["salary"]
competition_df = data["competition"]
sample_df = data["sample"]

st.title("Singapore Jobs Opportunity Dashboard")
st.caption(
    "For career consultants and trainers: find roles with stronger salary potential, "
    "healthy demand, and lower applicant competition."
)

st.sidebar.header("Filters")
categories = sorted(category_df["primary_category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Job Category", categories, default=[])
min_salary = int(title_df["median_salary"].min())
max_salary = int(title_df["median_salary"].max())
salary_range = st.sidebar.slider(
    "Median Salary Range",
    min_value=min_salary,
    max_value=max_salary,
    value=(min_salary, max_salary),
    step=500,
)
max_applications = st.sidebar.slider(
    "Maximum Avg Applications",
    min_value=0.0,
    max_value=float(round(title_df["avg_applications"].quantile(0.95), 1)),
    value=float(round(title_df["avg_applications"].quantile(0.95), 1)),
    step=0.5,
)
keyword = st.sidebar.text_input("Job Title Keyword").strip().lower()
top_n = st.sidebar.slider("Top N Results", min_value=5, max_value=30, value=10)

category_filtered = filter_categories(category_df, selected_categories)
title_filtered = filter_categories(title_df, selected_categories)
monthly_filtered = filter_categories(monthly_df, selected_categories)
salary_filtered = filter_categories(salary_df, selected_categories)
competition_filtered = filter_categories(competition_df, selected_categories)
sample_filtered = filter_categories(sample_df, selected_categories)

title_filtered = title_filtered[
    title_filtered["median_salary"].between(salary_range[0], salary_range[1])
    & (title_filtered["avg_applications"] <= max_applications)
]
competition_filtered = competition_filtered[
    competition_filtered["median_salary"].between(salary_range[0], salary_range[1])
    & (competition_filtered["avg_applications"] <= max_applications)
]
if keyword:
    title_filtered = title_filtered[
        title_filtered["title_display"].str.lower().str.contains(keyword, na=False)
    ]
    competition_filtered = competition_filtered[
        competition_filtered["title_display"].str.lower().str.contains(keyword, na=False)
    ]
    sample_filtered = sample_filtered[
        sample_filtered["title_display"].str.lower().str.contains(keyword, na=False)
    ]

tab_overview, tab_demand, tab_salary, tab_competition, tab_finder = st.tabs(
    ["Overview", "Demand Trends", "Salary Analysis", "Competition", "Opportunity Finder"]
)

with tab_overview:
    metric_cols = st.columns(5)
    metric_cols[0].metric("Postings", f"{int(overview['total_postings']):,}")
    metric_cols[1].metric("Vacancies", f"{int(overview['total_vacancies']):,}")
    metric_cols[2].metric("Median Salary", f"${overview['median_salary']:,.0f}")
    metric_cols[3].metric("Avg Applications", f"{overview['avg_applications']:.1f}")
    metric_cols[4].metric("Categories", f"{int(overview['category_count']):,}")

    left, right = st.columns(2)
    with left:
        top_categories = category_filtered.sort_values("postings", ascending=False).head(top_n)
        fig = px.bar(
            top_categories,
            x="postings",
            y="primary_category",
            orientation="h",
            color="opportunity_score",
            color_continuous_scale="Greens",
            title="Top Categories by Postings",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        top_titles = title_filtered.sort_values("postings", ascending=False).head(top_n)
        fig = px.bar(
            top_titles,
            x="postings",
            y="title_display",
            orientation="h",
            color="median_salary",
            color_continuous_scale="Blues",
            title="Top Job Titles by Postings",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("Preview Sample Jobs"):
        st.dataframe(sample_filtered.head(500), use_container_width=True, height=350)

with tab_demand:
    monthly_total = (
        monthly_filtered.groupby("posting_month", as_index=False)
        .agg(postings=("postings", "sum"), total_vacancies=("total_vacancies", "sum"))
        .sort_values("posting_month")
    )
    fig = px.line(monthly_total, x="posting_month", y="postings", markers=True, title="Monthly Job Postings")
    st.plotly_chart(fig, use_container_width=True)

    top_trend_categories = category_filtered.sort_values("postings", ascending=False).head(8)[
        "primary_category"
    ]
    trend_by_category = monthly_filtered[monthly_filtered["primary_category"].isin(top_trend_categories)]
    fig = px.line(
        trend_by_category,
        x="posting_month",
        y="postings",
        color="primary_category",
        title="Demand Trend by Top Categories",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab_salary:
    left, right = st.columns(2)
    with left:
        salary_by_category = category_filtered.sort_values("median_salary", ascending=False).head(top_n)
        fig = px.bar(
            salary_by_category,
            x="median_salary",
            y="primary_category",
            orientation="h",
            color="median_salary",
            color_continuous_scale="Greens",
            title="Highest Median Salary by Category",
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        salary_by_seniority = (
            salary_filtered.groupby("seniority_group", as_index=False)
            .agg(median_salary=("median_salary", "median"), postings=("postings", "sum"))
            .sort_values("median_salary", ascending=False)
        )
        fig = px.bar(
            salary_by_seniority,
            x="seniority_group",
            y="median_salary",
            color="postings",
            color_continuous_scale="Blues",
            title="Median Salary by Seniority",
        )
        st.plotly_chart(fig, use_container_width=True)

    top_paid = title_filtered.sort_values("median_salary", ascending=False).head(top_n)
    st.subheader("Top Paying Roles")
    st.dataframe(
        top_paid[
            [
                "title_display",
                "primary_category",
                "postings",
                "median_salary",
                "avg_applications",
                "opportunity_score",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tab_competition:
    left, right = st.columns(2)
    with left:
        low_comp = competition_filtered.sort_values("avg_applications").head(top_n)
        fig = px.bar(
            low_comp,
            x="avg_applications",
            y="title_display",
            orientation="h",
            color="median_salary",
            color_continuous_scale="Greens",
            title="Lowest Competition Roles",
        )
        fig.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig, use_container_width=True)
    with right:
        fig = px.scatter(
            competition_filtered.head(3000),
            x="avg_applications",
            y="median_salary",
            size="postings",
            color="competition_level",
            hover_name="title_display",
            title="Salary vs Applicant Competition",
            color_discrete_map={"Low": "#2ca25f", "Medium": "#fdae61", "High": "#de2d26"},
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_finder:
    st.subheader("Best-Paid, Lower-Competition Opportunities")
    ranked = title_filtered.sort_values("opportunity_score", ascending=False).head(top_n)
    ranked_display = ranked[
        [
            "title_display",
            "primary_category",
            "postings",
            "total_vacancies",
            "median_salary",
            "avg_applications",
            "avg_views",
            "opportunity_score",
        ]
    ].copy()
    st.dataframe(
        ranked_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "title_display": st.column_config.TextColumn("Job Title"),
            "primary_category": st.column_config.TextColumn("Category"),
            "postings": st.column_config.NumberColumn("Postings", format="%d"),
            "total_vacancies": st.column_config.NumberColumn("Vacancies", format="%d"),
            "median_salary": st.column_config.NumberColumn("Median Salary", format="$%d"),
            "avg_applications": st.column_config.NumberColumn("Avg Applications", format="%.1f"),
            "avg_views": st.column_config.NumberColumn("Avg Views", format="%.1f"),
            "opportunity_score": st.column_config.ProgressColumn(
                "Opportunity Score",
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
        },
    )

    csv = ranked.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Opportunity Shortlist",
        data=csv,
        file_name="singapore_jobs_opportunity_shortlist.csv",
        mime="text/csv",
    )
