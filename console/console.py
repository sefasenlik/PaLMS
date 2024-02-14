### FLASK LIBRARIES
from flask import Flask, render_template, request

### PYTHON LIBRARIES
import xml.etree.ElementTree as ET
from lxml import etree

### PYTHON SECTION
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

### FLASK SECTION
app = Flask(__name__)

@app.route('/')
def home():
    buttons = extract_buttons_from_file(file_path)
    return render_template('buttons.html', buttons=buttons)

@app.route('/update_xml', methods=['POST'])
def update_xml():

    file_path = 'files/student_proposal_views.xml'
    button_index = int(request.form.get('button_index'))
    attributes = request.form.to_dict()
    del attributes['button_index']

    tree = etree.parse(file_path)
    buttons = list(tree.iter('button'))
    button = buttons[button_index]
    for key, value in attributes.items():
        button.set(key, value)

    tree.write(file_path)

    return 'XML file updated', 200