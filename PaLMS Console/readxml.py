import xml.etree.ElementTree as ET

file_path = 'files/student_proposal_views.xml'

def extract_buttons(xml_string):
    root = ET.fromstring(xml_string)
    buttons = []

    for record in root.iter('record'):
        record_id = record.get('id')
        if record_id.endswith('form'):
            for button in record.iter('button'):
                buttons.append(button.attrib)

    return buttons

def extract_buttons_from_file(file_path):
    with open(file_path, 'r') as file:
        xml_string = file.read()
    return extract_buttons(xml_string)

buttons = extract_buttons_from_file(file_path)

for button in buttons:
    print(button)