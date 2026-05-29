from shiny import render, reactive
from shiny.express import ui, input
import json
import logging
import sys
import traceback
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,
)

def _log_unhandled(exc_type, exc_value, exc_tb):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_tb)
        return
    logging.critical(
        "Unhandled exception:\n%s",
        "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
    )

sys.excepthook = _log_unhandled

EXAM_COLORS = {
    'A': '#1f77b4',
    'B': '#ff7f0e',
    'C': '#2ca02c',
    'D': '#d62728',
    'E': '#9467bd',
    'F': '#8c564b',
    'G': '#e377c2',
    'H': '#7f7f7f',
    'I': '#bcbd22',
}


def apply_bar_style(fig):
    fig.update_layout(
        xaxis=dict(tickformat="d"),
        yaxis=dict(tickformat="d"),
        font=dict(family="Arial, sans-serif", size=13, color="#333333"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        title=dict(font=dict(size=16), x=0.5, xanchor="center"),
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(size=15, family="Arial Bold, sans-serif"),
        marker=dict(line=dict(width=0)),
    )
    return fig

exams = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

# --- File readers for pre-computed analysis results ---

@reactive.file_reader("./analysis/study_programmes.json")
def study_programme_read():
    with open("./analysis/study_programmes.json", encoding='utf-8') as f:
        return json.load(f)

@reactive.file_reader("./analysis/exams_co_occurrence.json")
def exams_co_occurrence_read():
    with open("./analysis/exams_co_occurrence.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {tuple(k.split("|")): v for k, v in raw.items()}

@reactive.file_reader("./analysis/overall_exam_count_dist.json")
def overall_exam_count_dist_read():
    with open("./analysis/overall_exam_count_dist.json", encoding='utf-8') as f:
        return {int(k): v for k, v in json.load(f).items()}

@reactive.file_reader("./analysis/participant_exam_count_dist.json")
def participant_exam_count_dist_read():
    with open("./analysis/participant_exam_count_dist.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {exam: {int(k): v for k, v in dist.items()} for exam, dist in raw.items()}

@reactive.file_reader("./analysis/wish_distribution.json")
def wish_distribution_read():
    with open("./analysis/wish_distribution.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {exam: {int(k): v for k, v in dist.items()} for exam, dist in raw.items()}

@reactive.file_reader("./analysis/wish_count_distribution.json")
def wish_count_distribution_read():
    with open("./analysis/wish_count_distribution.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {category: {int(k): v for k, v in dist.items()} for category, dist in raw.items()}

@reactive.file_reader("./analysis/study_programme_co_occurrence.json")
def study_programme_co_occurrence_read():
    with open("./analysis/study_programme_co_occurrence.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {tuple(k.split("|")): v for k, v in raw.items()}

@reactive.file_reader("./analysis/sp_exam_count_dist.json")
def sp_exam_count_dist_read():
    with open("./analysis/sp_exam_count_dist.json", encoding='utf-8') as f:
        raw = json.load(f)
    return {sp: {int(k): v for k, v in dist.items()} for sp, dist in raw.items()}

# --- Lightweight reactive calcs (filtering only) ---

@reactive.calc
def study_programme_dataset() -> dict:
    return study_programme_read()

@reactive.calc
def selected_exam():
    return input.exam()

@reactive.calc
def exams_co_occurrence():
    return exams_co_occurrence_read()

@reactive.calc
def exam_co_occurrence_distribution():
    co_occurrence = exams_co_occurrence_read()
    exam = selected_exam()
    return {e2: count for (e1, e2), count in co_occurrence.items() if e1 == exam}

@reactive.calc
def participant_exam_count_distribution():
    return participant_exam_count_dist_read()

@reactive.calc
def participant_exam_study_programme_distribution():
    return sp_exam_count_dist_read()

@reactive.calc
def wish_distribution():
    return wish_distribution_read().get(selected_exam(), {})

@reactive.calc
def wish_count_distribution():
    return wish_count_distribution_read()

@reactive.calc
def selected_study_programme():
    return input.study_programme()

@reactive.calc
def study_programme_co_occurrence_distribution():
    co_occurrence = study_programme_co_occurrence_read()
    study_programme = selected_study_programme()
    return {sp2: count for (sp1, sp2), count in co_occurrence.items() if sp1 == study_programme}

@reactive.calc
def get_selectize_choices_uni():
    study_programme_data = study_programme_dataset()
    universities = set(sp['university'] for sp in study_programme_data.values())
    return {uni: uni for uni in universities}

with ui.nav_panel("Yleiskatsaus"):
    @render_plotly
    def co_occurrence_heatmap():
        co_occurrence = exams_co_occurrence()
        exams = sorted(set(exam for exam_pair in co_occurrence.keys() for exam in exam_pair))
        exam_index = {exam: idx for idx, exam in enumerate(exams)}

        matrix = [[0] * len(exams) for _ in range(len(exams))]

        for (exam1, exam2), count in co_occurrence.items():
            i, j = exam_index[exam1], exam_index[exam2]
            matrix[i][j] = count
            matrix[j][i] = count


        fig = px.imshow(
            matrix,
            x=exams,
            y=exams,
            color_continuous_scale='Blues',
            title="Valintakokeiden yhteishakujen lämpökartta"
        )
        
        fig.update_layout(
            width=700,
            height=700,
            margin=dict(l=100, r=150, t=80, b=100)
        )

        return fig
    
    @render_plotly
    def participant_exam_count_histogram_overview():
        distribution = overall_exam_count_dist_read()

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig = px.bar(
            x=keys,
            y=values,
            title="Hakijoiden valintakokeiden määrä",
            text_auto=True,
            labels={
                'x': 'Valintakokeiden määrä',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)
    
    ui.input_switch("exam_switch", "Tarkastele vain yliopistojen valintakokeita käyttäviä hakutoiveita", False) 

    @render_plotly
    def wish_histogram_overview():
        distribution = wish_count_distribution()

        if input.exam_switch():
            keys = sorted(distribution["known"].keys())
            values = [distribution["known"][k] for k in keys]
            title = 'Hakutoiveiden määrä (vain yliopistojen valintakokeita käyttävät hakukohteet)'
        else:
            keys = sorted(distribution["all"].keys())
            values = [distribution["all"][k] for k in keys]
            title = 'Hakutoiveden määrä (kaikki hakukohteet)'

        fig = px.bar(
            x=keys,
            y=values,
            title=title,
            text_auto=True,
            labels={
                'x': 'Hakutoiveiden määrä',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)
        


with ui.nav_panel("Koekohtainen tarkastelu"):
    ui.input_select(  
        "exam",  
        "Valitse valintakoe:",  
        {
            "A": "Valintakoe A",
            "B": "Valintakoe B",
            "C": "Valintakoe C",
            "D": "Valintakoe D",
            "E": "Valintakoe E",
            "F": "Valintakoe F",
            "G": "Valintakoe G",
            "H": "Valintakoe H",
            "I": "Valintakoe I"
        }
    )

    @render_plotly
    def exam_co_occurrence_histogram():
        distribution = exam_co_occurrence_distribution()

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig = px.bar(
            x=keys,
            y=values,
            title=f"Valintakokeen {selected_exam()} hakijoiden muut valintakokeet",
            text_auto=True,
            labels={
                'x': 'Valintakoe',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)
    
    @render_plotly
    def participant_exam_count_histogram():
        distribution = participant_exam_count_distribution()
        exam = selected_exam()

        keys = sorted(distribution[exam].keys())
        values = [distribution[exam][k] for k in keys]

        fig = px.bar(
            x=keys,
            y=values,
            title=f"Valintakokeen {exam} hakijoiden valintakokeiden määrä",
            text_auto=True,
            labels={
                'x': 'Valintakokeiden määrä',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)
    
    @render_plotly
    def wish_histogram():
        distribution = wish_distribution()

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig = px.bar(
            x=keys,
            y=values,
            title=f"Millä prioriteetilla ensimmäinen valintakokeeseen {selected_exam()} liittyvä hakukohde on",
            text_auto=True,
            labels={
                'x': 'Prioriteetti',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)
    
@reactive.effect
def update_study_programmes():
    study_programme_data = study_programme_dataset()
    university = input.university()

    if university:
        filtered = {k: v for k, v in study_programme_data.items() if v['university'] == university}
    else:
        filtered = study_programme_data

    choices = {sp['id']: sp['name'] for sp in filtered.values()}
    ui.update_selectize("study_programme", choices=choices)

@reactive.effect
def update_universities():
    choices = get_selectize_choices_uni()
    ui.update_selectize("university", choices=choices)

with ui.nav_panel("Hakukohteet"):
    ui.input_selectize("university", "Valitse yliopisto:", choices={})
    ui.input_selectize("study_programme", "Valitse hakukohde:", choices={})


    @render.text
    def participants_study_programme():
        study_programme_data = study_programme_dataset()
        sp_exam_count = sp_exam_count_dist_read()
        study_programme = selected_study_programme()

        count = sum(sp_exam_count.get(study_programme, {}).values())
        study_programme_name = study_programme_data[study_programme]['name'] if study_programme in study_programme_data else "tuntematon"

        return f"{count} hakijaa hakukohteeseen {study_programme_name}"
    
    @render_plotly
    def co_occurrence_treemap():
        distribution = study_programme_co_occurrence_distribution()
        study_programme_data = study_programme_dataset()
        study_programme = selected_study_programme()

        if not distribution:
            return px.treemap(title="Ladataan dataa...")

        top_filter = 20
        filtered_distribution = dict(sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:top_filter])

        selected_study_programme_data = study_programme_data.get(study_programme, {})

        data = []
        for sp, count in filtered_distribution.items():
            sp_name = study_programme_data[sp]['name'] if sp in study_programme_data else "tuntematon"
            university = study_programme_data[sp]['university'] if sp in study_programme_data else "tuntematon"
            exam_color = EXAM_COLORS.get(study_programme_data[sp]['exam'], '#333333') if sp in study_programme_data else '#333333'
            data.append({'study_programme': sp_name, 'university': university, 'label': f"{sp_name} ({university})", 'count': count, 'color': exam_color})

        sp_name = selected_study_programme_data.get('name', 'tuntematon')
        
        
        df = pd.DataFrame(data)

        fig = px.treemap(df,
                values='count',
                parents=[""] * len(df),
                ids='label',
                names='study_programme',
                title=f"Hakukohteen {sp_name} ristihakukohteet"
        )

        return fig

    @render_plotly
    def participant_exam_count_histogram_study_programme():
        distribution = participant_exam_study_programme_distribution()
        study_programme = selected_study_programme()

        keys = sorted(distribution[study_programme].keys())
        values = [distribution[study_programme][k] for k in keys]

        fig = px.bar(
            x=keys,
            y=values,
            title=f"Hakukohteen {study_programme_dataset().get(study_programme, {}).get('name', 'tuntematon')}\nhakijoiden valintakokeiden määrä",
            text_auto=True,
            labels={
                'x': 'Valintakokeiden määrä',
                'y': 'Hakijoita'
            }
        )

        return apply_bar_style(fig)