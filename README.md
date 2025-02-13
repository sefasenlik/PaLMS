# PALMS
<img src="https://github.com/sefasenlik/PaLMS/assets/43667807/a27ff24d-6e9c-4a50-bf22-e925e7257683" alt="PaLMS" width="300" align="left"/>

PaLMS (Project Administration and Learning Management System) is a comprehensive ERP project intended to cover various needs of higher education institutes as an Odoo module. The initial goal of the project is to provide an efficient and secure platform for students, professors, academic supervisors and program managers to handle course work and final qualification work submissions and workflows. Instead of using Excel tables for project publication or Telegram for communication, every party involved can handle any task related to the process on PaLMS platform itself. In the future, PaLMS is expected to be a highly customizable and versatile product that addresses other needs of higher education institutions as well.

In the current status of the project, there are 15 models in total which are `application`, `availability`, `campus`, `commission`, `defense`, `degree`, `faculty`, `grade`, `manager`, `professor, program`, `project`, `proposal`, `student` and `supervisor`. These models are encapsulated in a single module called “Student” _(technical representation among resource files is “student”, like “hr” for the “Discuss” module)_. Their purposes can be briefly explained as follows:
- **Application:** Handles project applications from students. Students can submit application to an eligible program if they are not already assigned to a program. If the application is not accepted or rejected by the professor, it is possible for students to cancel it. Professor can accept or reject an application they receive. Accepting an application means that the project will be assigned to this particular student and all the other applications will be rejected in favor of the elected one.
- **Availability:** Defines which level of students in which program can apply for the project. For example, a project could be defined so that it can be applied for as a ВКР (graduation qualification work) for final year students of the Master's in Data Science program.
- **Campus:** This model was added in anticipation that the project will be used in the future for multiple campuses of multiple universities. It does not hold a critical role in the current state of the project, and only includes which university the faculty belongs to and its location.
- **Committee:** Once a project is completed by the student under the guidance of the relevant professor, it has to go through a committee review in order to be graded and formally evaluated. These committees are formed by users in the role of manager in PALMS, as in practice, and they examine the project defenses in presentation format at the set date and time.
- **Defense:** It includes the date of the presentation and by whom the project will be presented. By adding such objects to the committees, managers gather and list the projects that the committees will evaluate.
- **Degree:** Represents the academic progress and level of education of the student (e.g. first-year Master’s degree). This model aids in determining the eligibility of students when they intend to apply to a published project.
- **Faculty:** Represents the highest level of academic hierarchy, encompassing professors, programs and more, providing a comprehensive structure for the higher education institute.
- **Grade:** Allows commission members to grade projects with confidentiality.
- **Manager:** Encapsulates the _res.users_ module that Odoo provides to regulate system users for the purpose of specifying program managers in PALMS. It is used to indicate that the user who logs into the system is a manager and has rights such as forming committees and browsing project results. 
- **Professor:** Defines a faculty professor, enriching the existing _res.users_ module as in the case of managers. Users of this type can accept proposals, submit projects, review student applications.
- **Program:** It describes the direction in which students study within faculties. It comprises of students and projects. Academic supervisors have control over this structure and their authority is limited to their own programs.
- **Project:** Projects stand out as the cornerstone of the PALMS business process and are by far the largest model of the system. Projects are created by professors, regulated by supervisors and completed by students. When projects are assigned to a student, a project.project model object with the same name is created in the Odoo system to facilitate task tracking and made accessible to the student and the professor.
The PALMS _student.project_ model, which addresses an academic purpose, should not be confused with _project.project_, Odoo's multipurpose task management module.
- **Proposal:** They are designed to enable students to submit their academic project ideas in a systematic way for professors' evaluation. Proposals are created by students and evaluated by professors. Approved proposals become projects.
- **Student:** Represents corresponding _res.users_ objects (of student user group) that send applications and be assigned to a project, for supervisor’s ease. 
- **Supervisor:** A collection of utility functions, views, and module functionalities shared across models, allowing easy code maintenance.

<img src="https://i.ibb.co/svkXsDmV/PALMSDiagram.png" alt="UML diagram of models of 'student' module, which are business objects declared as Python classes" width="750"/>

## Key Innovations

### 1. **Integrated ERP and LMS Functionality**
PALMS combines **Enterprise Resource Planning (ERP)** and **Learning Management System (LMS)** features into a single platform. It leverages Odoo's modular architecture to provide a comprehensive suite of tools for managing student projects, including:
- **Project submission, approval, and tracking**
- **Task management** for students and professors
- **Automated notifications** and communication channels
- **Customizable workflows** for different academic programs

### 2. **Low-Code Customization with PALMS Console**
PALMS introduces a **low-code customization console** built using **Flask**, allowing non-technical administrators to modify the system without writing code. The PALMS Console:
- **Parses Odoo module files** (Python and XML) to display interface elements (buttons, fields, etc.) in a user-friendly web interface.
- **Enables real-time modifications** to the system's user interface and workflows, making it adaptable to changing academic requirements.
- **Supports dynamic updates** to Odoo views and models, ensuring the system remains flexible and responsive to institutional needs.

### 3. **Streamlined Workflow Automation**
PALMS automates key processes in student project management, including:
- **Automatic project assignment** to supervisors upon submission.
- **Automated notifications** via email and internal messaging for key actions (e.g., project approval, application acceptance).
- **Task management integration** with Odoo's **Project** module, allowing students and professors to break down projects into smaller tasks and track progress.

### 4. **Role-Based Access and Security**
PALMS implements a robust **role-based access control (RBAC)** system to ensure data security and workflow integrity. Key user roles include:
- **Students**: Can view available projects, submit applications, and propose project ideas.
- **Professors**: Can create projects, evaluate student proposals, and manage project tasks.
- **Academic Supervisors**: Approve or reject projects and monitor student progress.
- **Administrators**: Have full control over the system, including the ability to modify workflows via the PALMS Console.

### 5. **Multi-Language Support**
PALMS supports **multi-language interfaces**, including **English** and **Russian**, making it accessible to a diverse user base. The system also supports **Cyrillic characters** in user inputs and UI elements.

### 6. **Scalable and Modular Architecture**
PALMS is designed to scale with the needs of large institutions. It supports:
- **Up to 10,000 users**, including 1,000 professors and 500 academic staff.
- **500 concurrent users** in the pilot phase, with potential for **5,000 simultaneous users** in full deployment.
- **Containerized deployment** using **Docker** and orchestration with **Kubernetes** for high availability and scalability.

## Technical Highlights

### 1. **Odoo ERP Platform**
PALMS is built on **Odoo**, a powerful open-source ERP platform. Key technical features include:
- **Modular Design**: PALMS is implemented as a custom Odoo module (`student`), integrating seamlessly with Odoo's existing modules (e.g., **Project**, **Discuss**, **Employees**).
- **Object-Relational Mapping (ORM)**: Odoo's ORM layer simplifies database interactions, allowing for efficient management of complex data structures.
- **Multi-Tier Architecture**: Odoo's architecture separates the **presentation layer** (HTML, CSS, JavaScript), **application layer** (Python), and **data layer** (PostgreSQL), ensuring optimal performance and scalability.

### 2. **Flask-Based PALMS Console**
The **PALMS Console** is a standalone Flask application that enhances Odoo's customization capabilities:
- **File Parsing**: The console reads and parses Odoo's `.xml` (view files) and `.py` (model files) to extract interface elements and their attributes.
- **User-Friendly Interface**: Administrators can modify buttons, fields, and workflows through a web-based interface without touching the source code.
- **Dynamic Updates**: Changes made in the console are reflected in the Odoo system after a server restart, ensuring seamless integration.

### 3. **Database Management with PostgreSQL**
PALMS uses **PostgreSQL** as its primary database, offering:
- **ACID Compliance**: Ensures data integrity and reliability.
- **Scalability**: Supports large datasets and high user concurrency.
- **JSONB Support**: Allows flexible schema design for complex data structures.

### 4. **Nginx for Load Balancing and SSL**
PALMS employs **Nginx** as a reverse proxy and load balancer to:
- **Distribute incoming traffic** across multiple Odoo instances.
- **Handle SSL/TLS encryption** for secure communication.
- **Support HTTP/2** for improved performance.

### 5. **Advanced Notification System**
PALMS integrates Odoo's **Discuss** module to provide:
- **Real-time messaging** between students, professors, and supervisors.
- **Automated email notifications** for key actions (e.g., project submission, application acceptance).
- **Action feedback** with confirmation dialog boxes and persistent reminders.

## System Features

### 1. **Customizable Academic Institute Structure**
- **Campuses**: Support for multiple campuses across different universities.
- **Faculties**: Management of faculties with dedicated academic staff (professors, supervisors, managers).
- **Academic Programs**: Management of programs, including students and their academic projects.

### 2. **Streamlined Project Lifecycle Management**
- **Project Draft Creation**: Professors create project drafts and submit them for approval.
- **Multi-Directional Submission**: Projects are evaluated independently by each program supervisor.
- **Regulated Application Process**: Students can apply for projects, with restrictions based on faculty, program, or academic progress.

### 3. **Task Management and Progress Tracking**
- **Task Creation**: Professors and students can create and assign tasks within projects.
- **Kanban Views**: Visualize task progress with Kanban boards.
- **Calendar Integration**: Track deadlines and milestones with calendar views.

### 4. **Commission Formation and Grading**
- **Commission Formation**: Managers can form commissions to evaluate completed projects.
- **Private Grading**: Commission members grade projects confidentially.
- **Final Grade Calculation**: Automatic and manual options for final grade determination.

### 5. **User Group-Specific Interfaces**
- **Personalized Dashboards**: Tailored views for students, professors, and supervisors.
- **Progress Tracking**: Kanban views and progress bars for monitoring project progress.

### 6. **Reporting and Analytics**
- **Program Manager Reports**: Visualization tools like pie charts and statistics for project evaluations and student performance.

## Architectural Diagrams

#### Main Workflow
<img src="https://i.ibb.co/fGFKd761/PALMS-Main-Object-Workflow.png" alt="Main workflow of the proposed solution, displaying Proposal, Project, Project Availability and Application business objects" width="750"/>

#### Use-case Diagram
<img src="https://i.ibb.co/0Vpkn0Mt/PALMSUse-Case-Diagram.png" alt="Use-case diagram of the intended system" width="750"/>

## Conclusion
PALMS represents a significant advancement in student project management for higher education institutions. By leveraging the flexibility of Odoo and the power of Flask, PALMS provides a scalable, customizable, and user-friendly solution that addresses the unique challenges of academic project management. Its low-code customization capabilities ensure that the system can adapt to evolving institutional needs, making it a sustainable and future-proof solution.

## Screenshots

<img src="https://i.ibb.co/DF3BgXG/SS1.png" alt="'Project Evaluation Board' with several projects of different stages" width="750"/>
<img src="https://i.ibb.co/JR64JrjT/SS2.png" alt="'Available Projects' view for students with 'Available for application' filter and ‘Approved for’ grouping enabled" width="750"/>
<img src="https://i.ibb.co/B2XBBRVW/SS3.png" alt="Project detail view in Russian UI showing 'Results' tab ('Faculty' menu is expanded)" width="750"/>
<img src="https://i.ibb.co/nNTVXZnf/SS4.png" alt="Grading interface for commission members" width="750"/>

---

## PALMS Console

<img src="https://github.com/sefasenlik/PaLMS/assets/43667807/1bcd6fa0-9792-4a15-a0fa-132bdf200c65" alt="PaLMS Console" width="150" align="left"/>

In order to turn PALMS into a sustainable solution and to enable it to adapt to changing conditions, it is necessary to provide an interface, especially for system administrators, where the features and settings of the application can be changed. This interface should be specifically designed to be able to tweak the functionality of PALMS and, if necessary, even change the existing business process. In order to add these features to the project and to create a low-code environment, a Flask web application has been developed that can directly interfere with the code of both the back-end and the front-end of the PALMS module.

The Flask application, named “PALMS Console”, serves as an interactive interface for visualizing and manipulating Odoo view files (.xml) and module files (.py). The application is designed to parse the structure of Odoo views and modules, display the content in a user-friendly format, and allow users to make changes that are reflected back to the original files.

### Project Report
For more information, please check the [project report](https://drive.google.com/file/d/1qv9msg0TLNRB6qGb0e-ZfZvuQzBm_fCg/view?usp=sharing).
