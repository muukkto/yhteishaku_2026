from shiny import render, reactive
from shiny.express import ui, input
import json
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly


@reactive.file_reader(filepath = "./analysis/study_programmes.json")
def study_programme_read(filepath = "./analysis/study_programmes.json"):
    return pd.read_json(filepath, orient='index', encoding='utf-8')

@reactive.file_reader(filepath = "./analysis/applications.json")
def applications_read(filepath = "./analysis/applications.json"):
    return pd.read_json(filepath, orient='index', encoding='utf-8')

@reactive.calc
def study_programme_dataset() -> dict:
    data = study_programme_read()
    json_data = data.to_json(orient='index')
    return json.loads(json_data)

@reactive.calc   
def applications_dataset() -> dict:
    data = applications_read()
    json_data = data.to_json(orient='index')
    return json.loads(json_data)

@reactive.calc
def selected_exam():
    return input.exam()

@reactive.calc
def exams_co_occurrence():
    study_programme_data = study_programme_dataset()
    application_data = applications_dataset()

    co_occurrence = {}

    for application in application_data.values():
        exams = set()
        for i in range(1, 7):
            study_programme = application["study_programmes"][str(i)]
            if study_programme is not None and study_programme in study_programme_data:
                exams.add(study_programme_data[study_programme]['exam'])
        
        for exam1 in exams:
            for exam2 in exams:
                if exam1 != exam2:
                    co_occurrence[(exam1, exam2)] = co_occurrence.get((exam1, exam2), 0) + 1

    return co_occurrence

@reactive.calc
def exam_co_occurrence_distribution():
    co_occurrence = exams_co_occurrence()
    exam = selected_exam()

    distribution = {}

    for (exam1, exam2), count in co_occurrence.items():
        if exam1 == exam:
            distribution[exam2] = distribution.get(exam2, 0) + count

    return distribution

@reactive.calc
def wish_distribution():
    study_programme_data = study_programme_dataset()
    application_data = applications_dataset()
    exam = selected_exam()

    distribution = {}
    
    for application in application_data.values():
        for i in range(1, 7):
            study_programme = application["study_programmes"][str(i)]
            if study_programme is not None and study_programme in study_programme_data:
                if study_programme_data[study_programme]['exam'] == exam:
                    distribution[i] = distribution.get(i, 0) + 1
                    break

    return distribution

@reactive.calc
def selected_study_programme():
    return input.study_programme()

@reactive.calc
def study_programme_co_occurrence():
    study_programme_data = study_programme_dataset()
    application_data = applications_dataset()
    co_occurrence = {}
    for application in application_data.values():
        study_programmes = set()
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp is not None and sp in study_programme_data:
                study_programmes.add(sp)

        for sp1 in study_programmes:
            for sp2 in study_programmes:
                if sp1 != sp2:
                    co_occurrence[(sp1, sp2)] = co_occurrence.get((sp1, sp2), 0) + 1

    return co_occurrence

@reactive.calc
def study_programme_co_occurrence_distribution():
    co_occurrence = study_programme_co_occurrence()
    study_programme = selected_study_programme()

    distribution = {}
    for (sp1, sp2), count in co_occurrence.items():
        if sp1 == study_programme:
            distribution[sp2] = distribution.get(sp2, 0) + count

    return distribution

#@render.plot
#def co_occurrence_heatmap():
    co_occurrence = exams_co_occurrence()
    exams = sorted(set(exam for exam_pair in co_occurrence.keys() for exam in exam_pair))
    exam_index = {exam: idx for idx, exam in enumerate(exams)}

    matrix = [[0] * len(exams) for _ in range(len(exams))]

    for (exam1, exam2), count in co_occurrence.items():
        i, j = exam_index[exam1], exam_index[exam2]
        matrix[i][j] = count
        matrix[j][i] = count

    fig, ax = plt.subplots()
    cax = ax.matshow(matrix, cmap='Blues')
    fig.colorbar(cax)

    ax.set_xticks(range(len(exams)))
    ax.set_yticks(range(len(exams)))
    ax.set_xticklabels(exams, rotation=90)
    ax.set_yticklabels(exams)

    ax.set_title("Valintakokeiden yhteishakujen lämpökartta")

    return fig

@reactive.calc
def get_selectize_choices_uni():
    study_programme_data = study_programme_dataset()
    universities = set(sp['university'] for sp in study_programme_data.values())
    choices = {uni: uni for uni in universities}
    return choices

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

    @render.plot
    def exam_co_occurrence_histogram():
        distribution = exam_co_occurrence_distribution()

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig, ax = plt.subplots()
        ax_container = ax.bar(keys, values)
        ax.bar_label(ax_container, label_type='center')

        ax.set_xlabel("Valintakoe")
        ax.set_ylabel("Hakijoita")
        ax.set_title(f"Valintakokeen {selected_exam()} hakijoiden muut valintakokeet")

        return fig
    
    @render.plot
    def wish_histogram():
        distribution = wish_distribution()

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig, ax = plt.subplots()
        ax.bar(keys, values)

        ax.set_xlabel("Hakutoive")
        ax.set_ylabel("Hakijoita")
        ax.set_title(f"Hakutoiveiden jakauma valintakokeessa {selected_exam()}")

        return fig
    
with ui.nav_panel("Hakutoiveet"):
    @render.ui
    def university_selector():
        choices = get_selectize_choices_uni()

        return ui.input_selectize(  
            "university",  
            "Valitse yliopisto:",  
            choices
        )
    
    ui.input_selectize("study_programme", "Valitse hakukohde:", choices={})

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

    @render.text
    def participants_study_programme():
        study_programme_data = study_programme_dataset()
        application_data = applications_dataset()
        study_programme = selected_study_programme()

        count = 0
        for application in application_data.values():
            for i in range(1, 7):
                if application["study_programmes"][str(i)] == study_programme:
                    count += 1
                    break

        study_programme_name = study_programme_data[study_programme]['name'] if study_programme in study_programme_data else "tuntematon"

        return f"{count} participants in study programme {study_programme_name}"
    
    @render_plotly
    def co_occurrence_treemap():
        distribution = study_programme_co_occurrence_distribution()
        study_programme_data = study_programme_dataset()
        study_programme = selected_study_programme()

        top_filter = 20
        filtered_distribution = dict(sorted(distribution.items(), key=lambda item: item[1], reverse=True)[:top_filter])

        data = []
        for sp, count in filtered_distribution.items():
            sp_name = study_programme_data[sp]['name'] if sp in study_programme_data else "tuntematon"
            university = study_programme_data[sp]['university'] if sp in study_programme_data else "tuntematon"
            data.append({'study_programme': sp_name, 'university': university, 'label': f"{sp_name} ({university})", 'count': count})

        df = pd.DataFrame(data)
        fig = px.treemap(df, 
                         path=['label'], 
                         values='count',
                         title=f"Co-occurring study programmes")
        return fig