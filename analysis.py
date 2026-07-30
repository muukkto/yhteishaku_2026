import json
import os


years = ["2025", "2026"]

for year in years:
    os.makedirs(f"./analysis/{year}", exist_ok=True)

    with open(f"./analysis/{year}/applications.json", encoding='utf-8') as f:
        applications = json.load(f)

    with open(f"./analysis/{year}/study_programmes.json", encoding='utf-8') as f:
        study_programmes = json.load(f)

    exam_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']

    # Exams per participant (intermediate, needed by multiple distributions)
    exams_by_participant = {}
    for application in applications.values():
        participant_exams = set()
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp and sp in study_programmes:
                participant_exams.add(study_programmes[sp]['exam'])
        exams_by_participant[application["id"]] = list(participant_exams)

    # 1. Exams co-occurrence matrix
    exams_co_occurrence = {}
    for pexams in exams_by_participant.values():
        for e1 in pexams:
            for e2 in pexams:
                if e1 != e2:
                    exams_co_occurrence[(e1, e2)] = exams_co_occurrence.get((e1, e2), 0) + 1

    # 2. Overall exam count distribution (all participants)
    overall_exam_count_dist = {}
    for pexams in exams_by_participant.values():
        count = len(pexams)
        overall_exam_count_dist[count] = overall_exam_count_dist.get(count, 0) + 1

    # 3. Participant exam count distribution per exam
    participant_exam_count_dist = {exam: {} for exam in exam_list}
    for pexams in exams_by_participant.values():
        count = len(pexams)
        for exam in pexams:
            participant_exam_count_dist[exam][count] = participant_exam_count_dist[exam].get(count, 0) + 1

    # 4. Wish distribution per exam (which priority slot the exam first appears at)
    wish_distribution = {exam: {} for exam in exam_list}
    for application in applications.values():
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp and sp in study_programmes:
                exam = study_programmes[sp]['exam']
                wish_distribution[exam][i] = wish_distribution[exam].get(i, 0) + 1
                break

    # 5. Wish count distribution (known/unknown/all study programmes per applicant)
    wish_count_dist = {"known": {}, "unknown": {}, "all": {}}
    for application in applications.values():
        known, unknown = 0, 0
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp:
                if sp in study_programmes:
                    known += 1
                else:
                    unknown += 1
        total = known + unknown
        wish_count_dist["known"][known] = wish_count_dist["known"].get(known, 0) + 1
        wish_count_dist["unknown"][unknown] = wish_count_dist["unknown"].get(unknown, 0) + 1
        wish_count_dist["all"][total] = wish_count_dist["all"].get(total, 0) + 1

    # 6. Study programme co-occurrence
    sp_co_occurrence = {}
    for application in applications.values():
        sps = set()
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp and sp in study_programmes:
                sps.add(sp)
        for sp1 in sps:
            for sp2 in sps:
                if sp1 != sp2:
                    sp_co_occurrence[(sp1, sp2)] = sp_co_occurrence.get((sp1, sp2), 0) + 1

    # 7. Participant exam count distribution per study programme
    sp_exam_count_dist = {sp: {} for sp in study_programmes}
    for application in applications.values():
        pid = application["id"]
        pexams = exams_by_participant[pid]
        count = len(pexams)
        for i in range(1, 7):
            sp = application["study_programmes"][str(i)]
            if sp and sp in study_programmes:
                sp_exam_count_dist[sp][count] = sp_exam_count_dist[sp].get(count, 0) + 1

    # --- Save results ---

    with open(f"./analysis/{year}/exams_co_occurrence.json", "w", encoding='utf-8') as f:
        json.dump({f"{k[0]}|{k[1]}": v for k, v in exams_co_occurrence.items()}, f, ensure_ascii=False)

    with open(f"./analysis/{year}/overall_exam_count_dist.json", "w", encoding='utf-8') as f:
        json.dump(overall_exam_count_dist, f, ensure_ascii=False)

    with open(f"./analysis/{year}/participant_exam_count_dist.json", "w", encoding='utf-8') as f:
        json.dump(participant_exam_count_dist, f, ensure_ascii=False)

    with open(f"./analysis/{year}/wish_distribution.json", "w", encoding='utf-8') as f:
        json.dump(wish_distribution, f, ensure_ascii=False)

    with open(f"./analysis/{year}/wish_count_distribution.json", "w", encoding='utf-8') as f:
        json.dump(wish_count_dist, f, ensure_ascii=False)

    with open(f"./analysis/{year}/study_programme_co_occurrence.json", "w", encoding='utf-8') as f:
        json.dump({f"{k[0]}|{k[1]}": v for k, v in sp_co_occurrence.items()}, f, ensure_ascii=False)

    with open(f"./analysis/{year}/sp_exam_count_dist.json", "w", encoding='utf-8') as f:
        json.dump(sp_exam_count_dist, f, ensure_ascii=False)

    print(f"Pre-computed statistics saved to ./analysis/{year}/")
