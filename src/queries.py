import pandas as pd
from sqlalchemy import text

from src.db import get_engine


def get_norm_table(
    variable_names=None,
    scale_max=None,
    gender=None,
    ses=None,
    category=None,
    sub_category=None,
    year=None,
):
    engine = get_engine()

    query = """
    SELECT DISTINCT
        variable_name,
        scale_max
    FROM responses
    """

    df = pd.read_sql(text(query), engine)

    if variable_names:
        df = df[df["variable_name"].isin(variable_names)]

    if scale_max:
        df = df[df["scale_max"] == scale_max]

    rows = []

    for _, row in df.iterrows():
        result = get_norm_by_percentile(
            variable_name=row["variable_name"],
            scale_max=int(row["scale_max"]),
            gender=gender,
            ses=ses,
            category=category,
            sub_category=sub_category,
            year=year,
        )

        if not result:
            continue

        mapping = {
            "Top 25%": result["top_25"],
            "Average 50%": result["avg_50"],
            "Bottom 25%": result["bot_25"],
        }

        for grade, stats in mapping.items():
            # FIX: dulu pakai `if not stats` yang selalu True untuk dict non-empty
            if not stats or stats["base_n"] == 0:
                continue

            rows.append(
                {
                    "Parameter": result["variable_name"],
                    "Skala": f"{result['scale_max']}pts",
                    "Norm Grade": grade,
                    "Base (N)": stats["base_n"],
                    "TB%": stats["tb_pct"],
                    "TB2%": stats["t2b_pct"],
                    "TB3%": stats["t3b_pct"],
                    "Mean Score": stats["mean_score"],
                }
            )

    return pd.DataFrame(rows)


def get_summary_stats():
    engine = get_engine()

    with engine.connect() as conn:
        project_count = conn.execute(
            text("""
            SELECT COUNT(DISTINCT project_id)
            FROM projects
        """)
        ).scalar()

        respondent_count = conn.execute(
            text("""
            SELECT COUNT(DISTINCT respondent_id)
            FROM responses
        """)
        ).scalar()

        response_count = conn.execute(
            text("""
            SELECT COUNT(*)
            FROM responses
        """)
        ).scalar()

        variable_count = conn.execute(
            text("""
            SELECT COUNT(DISTINCT variable_name)
            FROM responses
        """)
        ).scalar()

    return {
        "projects": project_count,
        "respondents": respondent_count,
        "responses": response_count,
        "variables": variable_count,
    }


def get_norm_by_percentile(
    variable_name: str,
    scale_max: int,
    category: str | None = None,
    sub_category: str | None = None,
    year: int | None = None,
    gender: str | None = None,
    ses: str | None = None,
) -> dict:
    """
    Hitung norm score by percentile untuk satu variable_name + scale_max.
    Return dict berisi Top 25%, Average 50%, Bottom 25% — masing-masing
    dengan TB%, T2B%, T3B%, dan Mean Score dalam skala asli.
    """

    filters = ["r.variable_name = :variable_name", "r.scale_max = :scale_max"]
    params = {"variable_name": variable_name, "scale_max": scale_max}

    if category:
        filters.append("p.category = :category")
        params["category"] = category
    if sub_category:
        filters.append("p.sub_category = :sub_category")
        params["sub_category"] = sub_category
    if year:
        filters.append("p.year = :year")
        params["year"] = year
    if gender:
        filters.append("r.gender = :gender")
        params["gender"] = gender
    if ses:
        filters.append("r.ses = :ses")
        params["ses"] = ses

    where_clause = " AND ".join(filters)

    query = f"""
        SELECT r.score
        FROM responses r
        JOIN projects p ON r.project_id = p.project_id
        WHERE {where_clause}
        ORDER BY r.score DESC;
    """

    engine = get_engine()
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)

    if df.empty:
        return {}

    total_n = len(df)
    top_n = max(1, round(total_n * 0.25))
    avg_n = max(1, round(total_n * 0.50))
    # FIX: bot_n sekarang dihitung dari sisa aktual, bukan rumus yang bisa hasilkan
    # nilai berbeda dari slice aktual — ini biar konsisten dengan slicing di bawah
    bot_n = max(0, total_n - top_n - avg_n)

    scores_sorted = df["score"].values  # sudah DESC dari query

    top_scores = scores_sorted[:top_n]
    avg_scores = scores_sorted[top_n : top_n + avg_n]
    bot_scores = scores_sorted[top_n + avg_n :]

    def compute_stats(scores, scale_max):
        n = len(scores)
        if n == 0:
            return {
                "base_n": 0,
                "tb_pct": None,
                "t2b_pct": None,
                "t3b_pct": None,
                "mean_score": None,
            }
        tb = round((scores >= scale_max).sum() / n * 100, 1)
        tb2 = round((scores >= scale_max - 1).sum() / n * 100, 1)
        tb3 = (
            round((scores >= scale_max - 2).sum() / n * 100, 1)
            if scale_max >= 7
            else None
        )
        mean = round(float(scores.mean()), 2)
        return {
            "base_n": n,
            "tb_pct": tb,
            "t2b_pct": tb2,
            "t3b_pct": tb3,
            "mean_score": mean,
        }

    return {
        "variable_name": variable_name,
        "scale_max": scale_max,
        "total_n": total_n,
        "top_25": compute_stats(top_scores, scale_max),
        "avg_50": compute_stats(avg_scores, scale_max),
        "bot_25": compute_stats(bot_scores, scale_max),
    }


def get_available_filters(engine=None) -> dict:
    """Ambil semua nilai unik untuk filter dropdown."""
    if engine is None:
        engine = get_engine()

    with engine.connect() as conn:
        categories = pd.read_sql(
            text("SELECT DISTINCT category FROM projects ORDER BY category"), conn
        )
        sub_cats = pd.read_sql(
            text("SELECT DISTINCT sub_category FROM projects ORDER BY sub_category"),
            conn,
        )
        years = pd.read_sql(
            text("SELECT DISTINCT year FROM projects ORDER BY year"), conn
        )
        variables = pd.read_sql(
            text(
                "SELECT DISTINCT variable_name, scale_max FROM responses ORDER BY variable_name, scale_max"
            ),
            conn,
        )
        genders = pd.read_sql(
            text(
                "SELECT DISTINCT gender FROM responses WHERE gender IS NOT NULL ORDER BY gender"
            ),
            conn,
        )
        ses_list = pd.read_sql(
            text(
                "SELECT DISTINCT ses FROM responses WHERE ses IS NOT NULL ORDER BY ses"
            ),
            conn,
        )

    return {
        "categories": categories["category"].dropna().tolist(),
        "sub_categories": sub_cats["sub_category"].dropna().tolist(),
        "years": years["year"].dropna().tolist(),
        "variables": variables.to_dict("records"),
        "variable_names": sorted(variables["variable_name"].dropna().unique().tolist()),
        "genders": genders["gender"].dropna().tolist(),
        "ses": ses_list["ses"].dropna().tolist(),
    }
