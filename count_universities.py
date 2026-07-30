with open("./analysis/applications.json", "r", encoding="utf-8") as f:
    applications = f.read()

with open("./analysis/study_programmes.json", "r", encoding="utf-8") as f:
    study_programmes = f.read()

import json

applications = json.loads(applications)
study_programmes = json.loads(study_programmes)

university_applications_all = {}
university_applications_once = {}

for application in applications:
    programmes = applications[application]["study_programmes"]
    application_universities = []
    for programme_id in programmes.values():
        if programme_id and programme_id in study_programmes.keys():
            programme_data = study_programmes[programme_id]
            university = programme_data["university"]

            university_applications_all[university] = university_applications_all.get(university, 0) + 1
            if university not in application_universities:
                university_applications_once[university] = university_applications_once.get(university, 0) + 1
                application_universities.append(university)


for university in university_applications_all.keys():
    count_all = university_applications_all[university]
    count_once = university_applications_once.get(university, 0)

    print(f"{university}: hakemukset: {count_all}, hakijat: {count_once}")
    