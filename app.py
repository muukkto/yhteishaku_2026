from shiny import render, reactive
from shiny.express import ui, input
import json
import os
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
import styles

YEARS = sorted([y for y in ["2025", "2026"] if os.path.isdir(f"./analysis/{y}")])
YEAR_CHOICES = {y: y for y in YEARS}
YEAR_COLORS = {"2025": "#636EFA", "2026": "#EF553B"}

exams = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]


def load_json(year, filename):
    with open(f"./analysis/{year}/{filename}", encoding="utf-8") as f:
        return json.load(f)

# --- Reactive inputs ---

@reactive.calc
def selected_exam():
    return input.exam()

@reactive.calc
def selected_study_programme():
    return input.study_programme()

@reactive.calc
def selected_year_heatmap():
    return input.year_heatmap()

@reactive.calc
def selected_year_hakukohteet():
    return input.year_hakukohteet()


# --- Year-specific data (Hakukohteet + heatmap) ---

@reactive.calc
def study_programme_data():
    return load_json(selected_year_hakukohteet(), "study_programmes.json")

@reactive.calc
def exams_co_occurrence_for_heatmap():
    raw = load_json(selected_year_heatmap(), "exams_co_occurrence.json")
    return {tuple(k.split("|")): v for k, v in raw.items()}

@reactive.calc
def sp_co_occurrence_for_year():
    raw = load_json(selected_year_hakukohteet(), "study_programme_co_occurrence.json")
    return {tuple(k.split("|")): v for k, v in raw.items()}

@reactive.calc
def sp_exam_count_dist_for_year():
    raw = load_json(selected_year_hakukohteet(), "sp_exam_count_dist.json")
    return {sp: {int(k): v for k, v in dist.items()} for sp, dist in raw.items()}


# --- Multi-year data (Yleiskatsaus + Koekohtainen bar charts) ---

@reactive.calc
def overall_exam_count_dist_all_years():
    result = {}
    for year in YEARS:
        raw = load_json(year, "overall_exam_count_dist.json")
        result[year] = {int(k): v for k, v in raw.items()}
    return result

@reactive.calc
def wish_count_distribution_all_years():
    result = {}
    for year in YEARS:
        raw = load_json(year, "wish_count_distribution.json")
        result[year] = {cat: {int(k): v for k, v in dist.items()} for cat, dist in raw.items()}
    return result

@reactive.calc
def exams_co_occurrence_for_exam_all_years():
    exam = selected_exam()
    result = {}
    for year in YEARS:
        raw = load_json(year, "exams_co_occurrence.json")
        co = {tuple(k.split("|")): v for k, v in raw.items()}
        result[year] = {e2: count for (e1, e2), count in co.items() if e1 == exam}
    return result

@reactive.calc
def participant_exam_count_dist_all_years():
    result = {}
    for year in YEARS:
        raw = load_json(year, "participant_exam_count_dist.json")
        result[year] = {ex: {int(k): v for k, v in dist.items()} for ex, dist in raw.items()}
    return result

@reactive.calc
def wish_distribution_all_years():
    result = {}
    for year in YEARS:
        raw = load_json(year, "wish_distribution.json")
        result[year] = {ex: {int(k): v for k, v in dist.items()} for ex, dist in raw.items()}
    return result


# --- Hakukohteet selectize updates ---

@reactive.effect
def update_universities():
    sp_data = study_programme_data()
    universities = sorted(set(sp["university"] for sp in sp_data.values()))
    ui.update_selectize("university", choices={u: u for u in universities})

@reactive.effect
def update_study_programmes():
    sp_data = study_programme_data()
    university = input.university_hakukohteet()
    filtered = {k: v for k, v in sp_data.items() if v["university"] == university} if university else sp_data
    ui.update_selectize("study_programme", choices={sp["id"]: sp["name"] for sp in filtered.values()})

@reactive.effect
def update_study_fields():
    sp_data = study_programme_data()
    study_fields = sorted(set(sp.get("study_field", "Tuntematon") for sp in sp_data.values()))
    ui.update_selectize("study_field", choices={sf: sf for sf in study_fields})

# --- UI ---

with ui.navset_tab():

    # ── Yleiskatsaus ────────────────────────────────────────────────────────────
    with ui.nav_panel("Yleiskatsaus"):

        ui.input_select("year_heatmap", "Valitse lämpökartan vuosi:", choices=YEAR_CHOICES)

        @render_plotly
        def co_occurrence_heatmap():
            co_occurrence = exams_co_occurrence_for_heatmap()
            sorted_exams = sorted(set(e for pair in co_occurrence.keys() for e in pair))
            idx = {e: i for i, e in enumerate(sorted_exams)}
            matrix = [[0] * len(sorted_exams) for _ in range(len(sorted_exams))]
            for (e1, e2), count in co_occurrence.items():
                matrix[idx[e1]][idx[e2]] = count
                matrix[idx[e2]][idx[e1]] = count
            fig = px.imshow(
                matrix,
                x=sorted_exams,
                y=sorted_exams,
                color_continuous_scale="Blues",
                title=f"Valintakokeiden yhteishakujen lämpökartta ({selected_year_heatmap()})",
            )
            fig.update_layout(width=700, height=700, margin=dict(l=100, r=150, t=80, b=100))
            return fig

        @render_plotly
        def participant_exam_count_histogram_overview():
            all_dists = overall_exam_count_dist_all_years()
            rows = []
            for year, dist in all_dists.items():
                total = sum(dist.values())
                for count, participants in dist.items():
                    rows.append({
                        "year": year,
                        "count": count,
                        "participants": participants,
                        "text": f"{participants} ({participants/total*100:.1f}%)" if total > 0 else str(participants),
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="count", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title="Hakijoiden valintakokeiden määrä",
                labels={"count": "Valintakokeiden määrä", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        ui.input_switch("exam_switch", "Tarkastele vain yliopistojen valintakokeita käyttäviä hakutoiveita", False)

        @render_plotly
        def wish_histogram_overview():
            all_dists = wish_count_distribution_all_years()
            key = "known" if input.exam_switch() else "all"
            title_suffix = (
                "(vain yliopistojen valintakokeita käyttävät hakukohteet)"
                if input.exam_switch()
                else "(kaikki hakukohteet)"
            )
            rows = []
            for year, cats in all_dists.items():
                dist = cats.get(key, {})
                total = sum(dist.values())
                for count, participants in dist.items():
                    rows.append({
                        "year": year,
                        "count": count,
                        "participants": participants,
                        "text": f"{participants} ({participants/total*100:.1f}%)" if total > 0 else str(participants),
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="count", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Hakutoiveiden määrä {title_suffix}",
                labels={"count": "Hakutoiveiden määrä", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

    # ── Koekohtainen tarkastelu ─────────────────────────────────────────────────
    with ui.nav_panel("Koekohtainen tarkastelu"):

        ui.input_select("exam", "Valitse valintakoe:", {e: f"Valintakoe {e}" for e in exams})

        @render_plotly
        def exam_co_occurrence_histogram():
            co_per_year = exams_co_occurrence_for_exam_all_years()
            exam = selected_exam()
            rows = []
            for year, dist in co_per_year.items():
                total = sum(dist.values())
                for e2, count in dist.items():
                    rows.append({
                        "year": year,
                        "exam": e2,
                        "participants": count,
                        "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count),
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="exam", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                category_orders={"exam": sorted(df["exam"].unique())},
                title=f"Valintakokeen {exam} hakijoiden muut valintakokeet",
                labels={"exam": "Valintakoe", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        @render_plotly
        def participant_exam_count_histogram():
            all_dists = participant_exam_count_dist_all_years()
            exam = selected_exam()
            rows = []
            for year, dists in all_dists.items():
                dist = dists.get(exam, {})
                total = sum(dist.values())
                for count, participants in dist.items():
                    rows.append({
                        "year": year,
                        "count": count,
                        "participants": participants,
                        "text": f"{participants} ({participants/total*100:.1f}%)" if total > 0 else str(participants),
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="count", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Valintakokeen {exam} hakijoiden valintakokeiden määrä",
                labels={"count": "Valintakokeiden määrä", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        @render_plotly
        def wish_histogram():
            all_dists = wish_distribution_all_years()
            exam = selected_exam()
            rows = []
            for year, dists in all_dists.items():
                dist = dists.get(exam, {})
                total = sum(dist.values())
                for priority, count in dist.items():
                    rows.append({
                        "year": year,
                        "priority": priority,
                        "participants": count,
                        "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count),
                    })
            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="priority", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Millä prioriteetilla ensimmäinen valintakokeeseen {exam} liittyvä hakukohde on",
                labels={"priority": "Prioriteetti", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

    # -- Yliopistokohtainen tarkastelu ───────────────────────────────────────────────
    with ui.nav_panel("Yliopistot"):
        @render_plotly
        def university_participant_count_histogram():
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    for university in set(
                        sp_data[application["study_programmes"][str(i)]]["university"]
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)] and application["study_programmes"][str(i)] in sp_data
                    ):
                        counts[university] = counts.get(university, 0) + 1
                total = sum(counts.values())
                for university, count in counts.items():
                    rows.append({"year": year, "university": university, "count": count, "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count)})

            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="university", y="count", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title="Hakijoiden määrä yliopistoittain",
                labels={"university": "Yliopisto", "count": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        ui.input_selectize("university", "Valitse yliopisto:", choices={})

        @render_plotly
        def university_exam_distribution():
            university = input.university()
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    for exam in set(
                        sp_data[application["study_programmes"][str(i)]]["exam"]
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)] and application["study_programmes"][str(i)] in sp_data
                        and sp_data[application["study_programmes"][str(i)]]["university"] == university
                    ):
                        counts[exam] = counts.get(exam, 0) + 1
                total = sum(counts.values())
                for exam, count in counts.items():
                    rows.append({"year": year, "exam": exam, "count": count, "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count)})

            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="exam", y="count", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                category_orders={"exam": sorted(df["exam"].unique())},
                title=f"Hakijoiden valintakokeiden jakauma {university}",
                labels={"exam": "Valintakoe", "count": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        @render_plotly
        def university_wish_distribution():
            university = input.university()
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    for i in range(1, 7):
                        sp_id = application["study_programmes"][str(i)]
                        if sp_id and sp_id in sp_data and sp_data[sp_id]["university"] == university:
                            counts[i] = counts.get(i, 0) + 1
                            break  # vain ensimmäinen osuma per hakija
                total = sum(counts.values())
                for priority, count in counts.items():
                    rows.append({"year": year, "priority": priority, "count": count, "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count)})

            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="priority", y="count", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Millä prioriteetilla ensimmäinen {university} liittyvä hakukohde on",
                labels={"priority": "Prioriteetti", "count": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

    # -- Koulutusalakohtainen tarkastelu ───────────────────────────────────────────────
    with ui.nav_panel("Koulutusalat"):
        ui.input_selectize("study_field", "Valitse koulutusala:", choices={})

        @render_plotly
        def study_field_exam_distribution():
            study_field = input.study_field()
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    # tarkista onko hakijalla hakukohde tällä koulutusalalla
                    has_study_field = any(
                        sp_data.get(application["study_programmes"][str(i)], {}).get("study_field") == study_field
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)]
                    )
                    if not has_study_field:
                        continue
                    # laske kaikki hakijan uniikit valintakokeet (yksi per hakija per koe)
                    for exam in set(
                        sp_data[application["study_programmes"][str(i)]]["exam"]
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)] and application["study_programmes"][str(i)] in sp_data
                    ):
                        counts[exam] = counts.get(exam, 0) + 1
                total = sum(counts.values())
                for exam, count in counts.items():
                    rows.append({"year": year, "exam": exam, "count": count, "text": f"{count} ({count/total*100:.1f}%)" if total > 0 else str(count)})

            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="exam", y="count", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                category_orders={"exam": sorted(df["exam"].unique())},
                title=f"Valintakokeiden jakauma koulutusalan {study_field} hakijoilla",
                labels={"exam": "Valintakoe", "count": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        @render_plotly
        def study_field_exam_count_distribution():
            study_field = input.study_field()
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    # tarkista onko hakijalla hakukohde tällä koulutusalalla
                    has_study_field = any(
                        sp_data.get(application["study_programmes"][str(i)], {}).get("study_field") == study_field
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)]
                    )
                    if not has_study_field:
                        continue
                    # laske hakijan uniikkien valintakokeiden määrä
                    unique_exams = set(
                        sp_data[application["study_programmes"][str(i)]]["exam"]
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)] and application["study_programmes"][str(i)] in sp_data
                    )
                    exam_count = len(unique_exams)
                    counts[exam_count] = counts.get(exam_count, 0) + 1
                total = sum(counts.values())
                for count, participants in counts.items():
                    rows.append({"year": year, "exam_count": count, "participants": participants, "text": f"{participants} ({participants/total*100:.1f}%)" if total > 0 else str(participants)})

            df = pd.DataFrame(rows)
            fig = px.bar(
                df, x="exam_count", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Valintakokeiden määrä koulutusalan {study_field} hakijoilla",
                labels={"exam_count": "Valintakokeiden määrä", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

        ui.input_switch("exam_switch_study_field", "Tarkastele vain yliopistojen valintakokeita käyttäviä hakutoiveita", False)

        @render_plotly
        def study_field_wish_histogram_overview():
            study_field = input.study_field()
            rows = []
            for year in YEARS:
                sp_data = load_json(year, "study_programmes.json")
                applications = load_json(year, "applications.json")
                counts = {}
                for application in applications.values():
                    # tarkista onko hakijalla hakukohde tällä koulutusalalla
                    has_study_field = any(
                        sp_data.get(application["study_programmes"][str(i)], {}).get("study_field") == study_field
                        for i in range(1, 7)
                        if application["study_programmes"][str(i)]
                    )
                    if not has_study_field:
                        continue
                    # laske hakijan hakutoiveiden määrä (kaikki tai vain tunnetut kytkimen mukaan)
                    if input.exam_switch_study_field():
                        wish_count = sum(
                            1 for i in range(1, 7)
                            if application["study_programmes"][str(i)] and application["study_programmes"][str(i)] in sp_data
                        )
                    else:
                        wish_count = sum(
                            1 for i in range(1, 7)
                            if application["study_programmes"][str(i)]
                        )
                    counts[wish_count] = counts.get(wish_count, 0) + 1
                total = sum(counts.values())
                for count, participants in counts.items():
                    rows.append({"year": year, "wish_count": count, "participants": participants, "text": f"{participants} ({participants/total*100:.1f}%)" if total > 0 else str(participants)})

            df = pd.DataFrame(rows)
            title_suffix = "(vain yliopistojen valintakokeita käyttävät hakukohteet)" if input.exam_switch_study_field() else "(kaikki hakukohteet)"
            fig = px.bar(
                df, x="wish_count", y="participants", color="year", barmode="group",
                text="text",
                color_discrete_map=YEAR_COLORS,
                title=f"Hakutoiveiden määrä koulutusalan {study_field} hakijoilla {title_suffix}",
                labels={"wish_count": "Hakutoiveiden määrä", "participants": "Hakijoita", "year": "Vuosi"},
            )
            return styles.apply_bar_style(fig)

    # ── Hakukohteet ─────────────────────────────────────────────────────────────
    with ui.nav_panel("Hakukohteet"):

        ui.input_select("year_hakukohteet", "Valitse vuosi:", choices=YEAR_CHOICES)
        ui.input_selectize("university_hakukohteet", "Valitse yliopisto:", choices={})
        ui.input_selectize("study_programme", "Valitse hakukohde:", choices={})

        @render.text
        def participants_study_programme():
            sp_data = study_programme_data()
            sp_exam_count = sp_exam_count_dist_for_year()
            study_programme = selected_study_programme()
            count = sum(sp_exam_count.get(study_programme, {}).values())
            sp_name = sp_data[study_programme]["name"] if study_programme in sp_data else "tuntematon"
            return f"{count} hakijaa hakukohteeseen {sp_name}"

        @render_plotly
        def co_occurrence_treemap():
            sp_data = study_programme_data()
            study_programme = selected_study_programme()
            distribution = {
                sp2: count
                for (sp1, sp2), count in sp_co_occurrence_for_year().items()
                if sp1 == study_programme
            }

            if not distribution:
                return px.treemap(title="Ladataan dataa...")

            top_filter = 20
            filtered = dict(sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:top_filter])
            sp_name = sp_data.get(study_programme, {}).get("name", "tuntematon")

            data = []
            for sp, count in filtered.items():
                name = sp_data[sp]["name"] if sp in sp_data else "tuntematon"
                university = sp_data[sp]["university"] if sp in sp_data else "tuntematon"
                color = styles.EXAM_COLORS.get(sp_data[sp]["exam"], "#333333") if sp in sp_data else "#333333"
                data.append({"study_programme": name, "university": university, "label": f"{name} ({university})", "count": count, "color": color})

            df = pd.DataFrame(data)
            fig = px.treemap(
                df,
                values="count",
                parents=[""] * len(df),
                ids="label",
                names="study_programme",
                color="color",
                title=f"Hakukohteen {sp_name} ristihakukohteet",
            )
            return fig

        @render_plotly
        def participant_exam_count_histogram_study_programme():
            sp_data = study_programme_data()
            distribution = sp_exam_count_dist_for_year()
            study_programme = selected_study_programme()

            dist = distribution.get(study_programme, {})
            keys = sorted(dist.keys())
            values = [dist[k] for k in keys]
            total = sum(values)
            text = [f"{v} ({v/total*100:.1f}%)" if total > 0 else str(v) for v in values]

            sp_name = sp_data.get(study_programme, {}).get("name", "tuntematon")
            fig = px.bar(
                x=keys,
                y=values,
                title=f"Hakukohteen {sp_name}\nhakijoiden valintakokeiden määrä",
                text=text,
                labels={"x": "Valintakokeiden määrä", "y": "Hakijoita"},
            )
            return styles.apply_bar_style(fig)
