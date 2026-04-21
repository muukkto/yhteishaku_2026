from shiny import render, reactive
from shiny.express import ui, input
import json
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly

exams = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

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
def exams_by_participant():
    study_programme_data = study_programme_dataset()
    application_data = applications_dataset()
    exams = {}

    for application in application_data.values():
        participant_exams = set()
        for i in range(1, 7):
            study_programme = application["study_programmes"][str(i)]
            if study_programme is not None and study_programme in study_programme_data:
                participant_exams.add(study_programme_data[study_programme]['exam'])

        exams[application["id"]] = participant_exams

    return exams

@reactive.calc
def participant_exam_count_distribution():
    exams_by_participant_data = exams_by_participant()
    distribution = {exam: {} for exam in exams}

    for exam in exams:
        for participant_exams in exams_by_participant_data.values():
            if exam in participant_exams:
                exam_count = len(participant_exams)
                distribution[exam][exam_count] = distribution[exam].get(exam_count, 0) + 1

    return distribution

@reactive.calc
def participant_exam_study_programme_distribution():
    exams_by_participant_data = exams_by_participant()
    application_data = applications_dataset()
    study_programme_data = study_programme_dataset()
    distribution = {study_programme: {} for study_programme in study_programme_data}

    for study_programme in study_programme_data:
        for application in application_data.values():
            for i in range(1, 7):
                if application["study_programmes"][str(i)] == study_programme:
                    participant_exams = exams_by_participant_data.get(application["id"], set())
                    exam_count = len(participant_exams)
                    distribution[study_programme][exam_count] = distribution[study_programme].get(exam_count, 0) + 1
                    break

    return distribution

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
def wish_count_distribution():
    study_programme_data = study_programme_dataset()
    application_data = applications_dataset()

    distribution = {"known": {}, "unknown": {}, "all": {}}

    j = 0

    for application in application_data.values():
        wish_count_known_study_programme = 0
        wish_count_unknown_study_programme = 0

        for i in range(1, 7):
            study_programme = application["study_programmes"][str(i)]
            if study_programme is not None:
                if study_programme in study_programme_data:
                    wish_count_known_study_programme += 1
                else:
                    wish_count_unknown_study_programme += 1

        wish_count_all_study_programme = wish_count_known_study_programme + wish_count_unknown_study_programme

        if wish_count_known_study_programme == 0:
            print(f"Application {j} has no known study programmes.")
            print(application)

        j += 1

        distribution["known"][wish_count_known_study_programme] = distribution["known"].get(wish_count_known_study_programme, 0) + 1
        distribution["unknown"][wish_count_unknown_study_programme] = distribution["unknown"].get(wish_count_unknown_study_programme, 0) + 1
        distribution["all"][wish_count_all_study_programme] = distribution["all"].get(wish_count_all_study_programme, 0) + 1

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

with ui.nav_panel("Yleiskatsaus"):
    @render.plot
    def co_occurrence_heatmap():
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
    
    @render.plot
    def participant_exam_count_histogram_overview():
        exams_by_participant_data = exams_by_participant()
        distribution = {}

        for participant_exams in exams_by_participant_data.values():
            exam_count = len(participant_exams)
            distribution[exam_count] = distribution.get(exam_count, 0) + 1

        keys = sorted(distribution.keys())
        values = [distribution[k] for k in keys]

        fig, ax = plt.subplots()
        ax_container = ax.bar(keys, values)
        ax.bar_label(ax_container, label_type='center')

        ax.set_xlabel("Valintakokeiden määrä")
        ax.set_ylabel("Hakijoita")
        ax.set_title("Hakijoiden valintakokeiden määrä")

        return fig
    
    ui.input_switch("exam_switch", "Tarkastele vain yliopistojen valintakokeita käyttäviä hakutoiveita", False) 

    @render.plot
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

        fig, ax = plt.subplots()
        ax_container = ax.bar(keys, values)

        ax.set_xlabel("Hakutoiveiden määrä")
        ax.set_ylabel("Hakijoita")
        ax.set_title(title)
        ax.bar_label(ax_container, label_type='center')

        return fig
        


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
    def participant_exam_count_histogram():
        distribution = participant_exam_count_distribution()
        exam = selected_exam()

        keys = sorted(distribution[exam].keys())
        values = [distribution[exam][k] for k in keys]

        fig, ax = plt.subplots()
        ax_container = ax.bar(keys, values)
        ax.bar_label(ax_container, label_type='center')

        ax.set_xlabel("Valintakokeiden määrä")
        ax.set_ylabel("Hakijoita")
        ax.set_title(f"Valintakokeen {exam} hakijoiden valintakokeiden määrä")

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
    
with ui.nav_panel("Hakukohteet"):
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

        return f"{count} hakijaa hakukohteeseen {study_programme_name}"
    
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

        sp_name = study_programme_data.get(study_programme, {}).get("name", "tuntematon")
        df = pd.DataFrame(data)
        fig = px.treemap(df, 
                         path=['label'], 
                         values='count',
                         title=f"Hakukohteen {sp_name} ristihakukohteet")
        return fig

    @render.plot
    def participant_exam_count_histogram_study_programme():
        distribution = participant_exam_study_programme_distribution()
        study_programme = selected_study_programme()

        keys = sorted(distribution[study_programme].keys())
        values = [distribution[study_programme][k] for k in keys]

        fig, ax = plt.subplots()
        ax_container = ax.bar(keys, values)
        ax.bar_label(ax_container, label_type='center')

        ax.set_xlabel("Valintakokeiden määrä")
        ax.set_ylabel("Hakijoita")
        sp_name = study_programme_dataset().get(study_programme, {}).get("name", "tuntematon")
        ax.set_title(f"Hakukohteen {sp_name}\nhakijoiden valintakokeiden määrä")

        return fig