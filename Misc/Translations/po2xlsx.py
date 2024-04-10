import xlsxwriter

def create_excel_file(input_text, output_file):
    # Create a new Excel workbook and add a worksheet
    workbook = xlsxwriter.Workbook(output_file)
    worksheet = workbook.add_worksheet()

    # Set column widths
    worksheet.set_column('A:A', 40)
    worksheet.set_column('B:B', 40)

    # Add headers
    worksheet.write('A1', 'msgid')
    worksheet.write('B1', 'msgstr')

    # Initialize row counter
    row = 1

    # Parse input text and write to Excel file
    lines = input_text.split('\n')
    msgid = ''
    for line in lines:
        if line.startswith('msgid'):
            # Start a new msgid
            msgid = line.split('msgid')[1]
        elif line.startswith('msgstr'):
            # Write previous msgid to Excel file
            if msgid:
                worksheet.write(row, 0, msgid)
                row += 1
        else:
            # Add to msgid (if it's a multi-line msgid)
            if msgid:
                msgid += line

    # Close the workbook
    workbook.close()

# Input file name
input_file = "ru.po"

# Read input text from file
with open(input_file, 'r', encoding='utf-8') as file:
    input_text = file.read()

# Output file name
output_file = "translations.xlsx"

# Create Excel file
create_excel_file(input_text, output_file)
print(f"Excel file '{output_file}' created successfully.")
