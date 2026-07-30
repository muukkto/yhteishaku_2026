import pandas as pd

exams = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]

for exam in exams:
    print(f"Processing exam: {exam}")
    parsed_rows = pd.read_excel(f'./data/2025/2025 Hakijat hakemuspalvelusta, valintakoe {exam}.xlsx')
    print(f"Parsed {len(parsed_rows)} rows for exam {exam}")
    hakukohteet = parsed_rows['Hakukohteet'].str.split("\n", expand=True)
    hakukohteet.columns = [f'Hakukohde {i+1}' for i in range(hakukohteet.shape[1])]
    parsed_rows = pd.concat([parsed_rows, hakukohteet], axis=1)
    str_cols = parsed_rows.select_dtypes(include='object').columns
    parsed_rows[str_cols] = parsed_rows[str_cols].apply(lambda col: col.str.replace('\n', ' ', regex=False))
    parsed_rows.to_csv(f'./data/2025/hakijat_{exam}.csv', index=False, sep=';', encoding='utf-8')

#for exam in exams:
#    print(f"Processing exam: {exam}")
#    parsed_rows = pd.read_excel(f'./data/2025/2025 Hakukohteet, valintakoe {exam}.xlsx')
#    print(f"Parsed {len(parsed_rows)} rows for exam {exam}")
#    str_cols = parsed_rows.select_dtypes(include='object').columns
#    parsed_rows[str_cols] = parsed_rows[str_cols].apply(lambda col: col.str.replace('\n', ' ', regex=False))
#    # Add column for exam
#    parsed_rows['Valintakoe'] = exam
#    parsed_rows.to_csv(f'./data/2025/valintakoe_{exam}.csv', index=False, sep=';', encoding='utf-8')