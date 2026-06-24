import re

import pandas as pd
from sqlalchemy.orm import Session

from src.db import get_engine
from src.schema import Project, Response

METADATA_COLS = [
    "SbjNum",
    "No Project",
    "Category",
    "Sub-Category",
    "Detail Product",
    "Gender",
    "Actual Age",
    "SES",
    "Occupation",
    "Type of Study",
    "Test Type",
    "Methodology",
    "Sub-Method",
    "# of Product",
    "Sequence",
]

VARIABLE_CANON = {
    "aftert\\aste": "aftertaste",
    "aftertaste.1": "aftertaste",
    "cofee aroma": "coffee aroma",
    "coffee taste.1": "coffee taste",
    "color.1": "color",
    "overal liking": "overall liking",
    "overal taste": "overall taste",
    "popcorn caramel ttaste": "popcorn caramel taste",
    "purchase intent w/ price.1": "purchase intent w/ price",
    "sovouriness": "savoriness",
    "balance taste": "balanced taste",
    "ease to bite": "easy to bite",
}

GENDER_CANON = {
    "laki-laki": "Male",
    "male": "Male",
    "perempuan": "Female",
    "female": "Female",
}

SES_CANON = {
    "a1": "Upper 1 (A)",
    "a2": "Upper 2 (B)",
    "b": "Upper 2 (B)",
    "upper 1 (a)": "Upper 1 (A)",
    "upper 2 (b)": "Upper 2 (B)",
    "middle 1 (c1)": "Middle 1 (C1)",
    "middle 2 (c2)": "Middle 2 (C2)",
    "middle 2 ()": "Middle 2 (C2)",
    "lower 1 (d)": "Lower 1 (D)",
}


def extract_scale(col_name: str) -> int | None:
    match = re.search(r"(\d+)\s*pts", col_name, re.IGNORECASE)
    return int(match.group(1)) if match else None


def normalize_score(score, scale_max: int) -> float:
    return round((score - 1) / (scale_max - 1), 4)


def clean_project_id(raw: str) -> str:
    return str(raw).strip()


def clean_respondent_id(raw) -> str | None:
    try:
        return str(int(float(str(raw).strip())))
    except (ValueError, TypeError):
        return None


def load_sheet(
    sheet_name: str, df: pd.DataFrame, engine, segment: str | None = None
) -> dict:
    df = df.loc[:, df.columns.notna()]
    df = df.loc[:, [c for c in df.columns if isinstance(c, str) and c.strip() != ""]]

    score_cols = [c for c in df.columns if c not in METADATA_COLS]

    stats = {"sheet": sheet_name, "projects": 0, "responses": 0, "skipped": 0}

    with Session(engine) as session:
        for _, row in df.iterrows():
            raw_pid = row.get("No Project")
            if pd.isna(raw_pid):
                stats["skipped"] += 1
                continue

            project_id = clean_project_id(raw_pid)
            respondent_id = clean_respondent_id(row.get("SbjNum"))
            if respondent_id is None:
                stats["skipped"] += 1
                continue

            year_match = re.search(r"(\d{4})", project_id)
            year = int(year_match.group(1)) if year_match else None

            if not session.get(Project, project_id):
                project = Project(
                    project_id=project_id,
                    year=year,
                    category=row.get("Category"),
                    sub_category=row.get("Sub-Category"),
                    detail_product=row.get("Detail Product"),
                    test_type=row.get("Test Type"),
                    methodology=row.get("Methodology"),
                    sub_method=row.get("Sub-Method"),
                )
                session.add(project)
                session.flush()
                stats["projects"] += 1

            for col in score_cols:
                raw_score = row.get(col)
                if pd.isna(raw_score):
                    continue

                scale_max = extract_scale(col)
                if scale_max is None:
                    continue

                variable_name = (
                    re.sub(r"\s*-?\s*\d+\s*pts?", "", col, flags=re.IGNORECASE)
                    .strip()
                    .lower()
                )
                variable_name = re.sub(
                    r"\s+", " ", variable_name
                )  # normalize spasi ganda
                variable_name = VARIABLE_CANON.get(variable_name, variable_name)

                score_val = float(raw_score)
                norm_val = normalize_score(score_val, scale_max)

                existing = (
                    session.query(Response)
                    .filter_by(
                        respondent_id=respondent_id,
                        project_id=project_id,
                        segment=segment,
                        variable_name=variable_name,
                    )
                    .first()
                )
                if existing:
                    continue

                response = Response(
                    respondent_id=respondent_id,
                    project_id=project_id,
                    segment=segment,
                    variable_name=variable_name,
                    scale_max=scale_max,
                    score=score_val,
                    score_normalized=norm_val,
                    gender=GENDER_CANON.get(
                        str(row.get("Gender")).strip().lower(),
                        str(row.get("Gender")).strip(),
                    )
                    if not pd.isna(row.get("Gender"))
                    else None,
                    actual_age=int(float(str(row.get("Actual Age")).strip()))
                    if not pd.isna(row.get("Actual Age"))
                    else None,
                    ses=SES_CANON.get(
                        str(row.get("SES")).strip().lower(), str(row.get("SES")).strip()
                    )
                    if not pd.isna(row.get("SES"))
                    else None,
                    occupation=str(row.get("Occupation")).strip()
                    if not pd.isna(row.get("Occupation"))
                    else None,
                )
                session.add(response)
                stats["responses"] += 1

        session.commit()

    return stats


def run_ingestion(filepath: str):
    engine = get_engine()
    xl = pd.ExcelFile(filepath)

    # Mapping sheet → segment (isi jika satu project punya beberapa segmen)
    SEGMENT_MAP = {
        "Parma Moms": "moms",
        "Parma Kids": "kids",
    }

    print(f"Memproses {len(xl.sheet_names)} sheet...\n")
    total_responses = 0

    for sheet_name in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet_name, header=1)
        segment = SEGMENT_MAP.get(sheet_name, None)
        result = load_sheet(sheet_name, df, engine, segment=segment)
        print(
            f"[{result['sheet']:<15}] projects: {result['projects']:>3} | "
            f"responses: {result['responses']:>6} | skipped: {result['skipped']:>3}"
        )
        total_responses += result["responses"]

    print(f"\nSelesai. Total responses masuk: {total_responses:,}")


if __name__ == "__main__":
    run_ingestion("data/raw/raw_data.xlsx")
