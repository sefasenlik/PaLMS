import openpyxl

# Load Excel file
excel_file = "translations.xlsx"
wb = openpyxl.load_workbook(excel_file)
ws = wb.active

# Read translations from Excel file
translations = list()
for row in ws.iter_rows(min_row=2, values_only=True):
    msgstr = row[1]
    translations.append(msgstr)

# Load .po file
po_file = "translations.po"
with open(po_file, "r", encoding="utf-8") as file:
    po_lines = file.readlines()

# Update .po file with translations
with open(po_file, "w", encoding="utf-8") as file:
    translation_index = 0
    for line in po_lines:
        if line.startswith('msgstr'):
            file.write(f'msgstr{translations[translation_index]}\n')
            translation_index = translation_index+1
        else:
            file.write(line)
