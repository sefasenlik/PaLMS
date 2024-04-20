## FLASK LIBRARIES
from flask import Flask, render_template, request

## PYTHON LIBRARIES
import xml.etree.ElementTree as ET
from lxml import etree

## PYTHON SECTION
xml_file_path = 'files/student_proposal_views.xml'
py_file_path = 'files/student_proposal.py'

### Buttons
def extract_buttons(xml_string):
    root = ET.fromstring(xml_string)
    buttons = []

    for record in root.iter('record'):
        record_id = record.get('id')
        if record_id.endswith('form'):
            for button in record.iter('button'):
                buttons.append(button.attrib)

    return buttons

def extract_buttons_from_file(xml_file_path):
    with open(xml_file_path, 'r') as file:
        xml_string = file.read()
    return extract_buttons(xml_string)

### Fields
def extract_fields(xml_string):
    root = ET.fromstring(xml_string)
    fields = {}

    for record in root.iter('record'):
        record_id = record.get('id')
        if record_id.endswith('form'):
            # Extract fields from groups
            for group in record.iter('group'):
                inner_group = group.find('group')
                if inner_group is None:
                    group_name = group.get('string', 'Unnamed Groups')
                    fields[group_name] = fields.get(group_name, [])
                    for field in group.iter('field'):
                        fields[group_name].append(field.attrib)
            # Extract fields from notebook
            for notebook in record.iter('notebook'):
                for page in notebook.iter('page'):
                    page_name = page.get('string', 'Unnamed Pages')
                    fields[page_name] = fields.get(page_name, [])
                    for field in page.iter('field'):
                        fields[page_name].append(field.attrib)

    return fields

def extract_fields_from_file(xml_file_path):
    with open(xml_file_path, 'r') as file:
        xml_string = file.read()
    return extract_fields(xml_string)

### Fields Details
def extract_field_details(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    field_details = {}
    for line in lines:
        if 'fields.' in line:
            field_name = line.split('=')[0].strip()
            field_type = line.split('fields.')[1].split('(')[0].strip()
            if "string=" in line:
                string_value = line.split("string=")[1].split(',')[0].strip()
            else:
                string_value = line.split('fields.')[1].split('(')[1].split(',')[0].strip()

            # Remove unwanted characters
            string_value = string_value.replace("'", "").replace('"', '').replace('(', '')

            field_details[field_name] = {'string': string_value, 'field_type': field_type}

    return field_details

## FLASK SECTION
app = Flask(__name__)

@app.route('/')
def home():
    buttons = extract_buttons_from_file(xml_file_path)
    fields = extract_fields_from_file(xml_file_path)
    field_details = extract_field_details(py_file_path)
    return render_template('mock_view.html', buttons=buttons, fields=fields, field_details=field_details)

@app.route('/update_xml', methods=['POST'])
def update_xml():

    button_index = int(request.form.get('button_index'))
    attributes = request.form.to_dict()
    del attributes['button_index']

    tree = etree.parse(xml_file_path)
    buttons = list(tree.iter('button'))
    button = buttons[button_index]
    for key, value in attributes.items():
        button.set(key, value)

    tree.write(xml_file_path)

    return 'XML file updated', 200