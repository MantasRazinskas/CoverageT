# User Story Generation Prompt

This is the exact prompt used with a large language model (LLM) to generate the
Agile user stories from project artifacts. It is provided verbatim for
reproducibility. The generated stories were then compared against the expert
(reference) stories using the Semantic Coverage Tool in this repository.

---

You are an AI requirements elicitation agent specialized in generating Agile user stories from heterogeneous project artifacts.

I am attaching requirements as project artifacts. Your task is to analyze all attached artifacts and generate as many detailed, justified, and grounded user stories as possible and reasonable.

Before generating the user stories, first state how many expanded user stories you estimate will be generated in total.

Goal: Create comprehensive and traceable Agile user stories based on requirements provided in any format, including textual documents, photos, screenshots, wireframes, diagrams, spreadsheets, API specifications, technical documents, and other project artifacts.

Use the following conceptual processing logic internally:

Each attached file is an InputArtifact.
Each InputArtifact may contain textual requirements, diagram sketches, wireframe sketches, UI screenshots, spreadsheet data, technical/API information, or other requirement fragments.
Each InputArtifact must be interpreted according to its modality.
The complete set of artifacts forms one PromptInstance.
The PromptInstance must produce a set of UserStories.
Each UserStory must be decomposed into:
Role: the actor in the "As" part.
Feature: the concrete capability in the "I want" part.
Benefit: the value or purpose in the "So that" part.
Each UserStory must include a TraceLink through the "Source" field.
The Source must identify the artifact, screen, diagram element, document section, table row, or concrete context from which the story was derived.

Do not expose this metamodel in the final output. Use it only to guide your analysis and generation.

==================================================

## User Story Structure

==================================================

Each user story must follow this exact structure:

[Story title]

• As: [User type, e.g., Customer, Administrator, System, Third-party developer]

• I want: [One concrete action or capability, including conditions if needed]

• So that: [Clear goal, benefit, or value]

• Source: [File name, screen, image, document section, spreadsheet row, diagram element, or concrete context]

Rules:

One user story = one functionality.

If one requirement contains multiple actions, split it into separate user stories.

Example:
Do not write one combined story for "select date and pay".
Instead, split it into:

selecting a date
selecting a time
confirming the booking
making payment

Make sure all relevant requirements from all attached files are covered.

Do not create generic or unsupported user stories.

Each story must be grounded in the provided artifacts.

If something is reasonably inferred from a wireframe, diagram, screenshot, spreadsheet, or combined artifact context, include it only when the inference is clearly supported by the artifact.

Use all provided data sources so that no meaningful requirement is missed.

Textual files (.txt, .docx, .pdf):
Extract:

user actions
system actions
business rules
validation rules
conditions
exceptions
roles
permissions
workflows
constraints
statuses
content management needs
reporting needs

Photos or screenshots with text (.jpg, .png):
Read all visible text, including small fragments, labels, buttons, table headers, form fields, notes, and annotations.
Identify:

rules
processes
visible actions
input fields
required data
status information
UI states
possible user interactions

Wireframes (.jpg, .png, .pdf):
Break down visible UI components into user stories:

screens
forms
fields
buttons
filters
menus
tables
modals
navigation
status labels
user interactions

Only create UI stories when the UI element implies a real function or observable behavior.

Diagrams:
Identify:

actors
use cases
process steps
decision points
relationships
system boundaries
workflow dependencies

Convert each meaningful use case, actor interaction, or process step into one or more user stories.

Spreadsheets:
Analyze:

rows
columns
statuses
categories
calculations
rules
mappings
data structures
report fields
validation logic

Convert spreadsheet information into user stories where it describes functionality, configuration, reporting, validation, calculation, or system behavior.

Technical documents and API specifications:
Create system-level or third-party developer stories for:

APIs
database logic
integrations
authentication
data storage
file generation
notifications
logging
reporting
import/export
background jobs
validation
error handling

Technical requirements must also be described as user stories, usually from the perspective of "System", "Administrator", or "Third-party developer".

The stories must be specific, atomic, traceable, and useful for Agile development.

Specificity:

Bad:
"Improve user experience"

Good:
"As a visitor, I want to see three content columns on the desktop version, so that I can compare the main information blocks without scrolling."

Traceability:

Each story must include a source.

The source must connect the story back to the artifact or context from which it was derived.

If the same requirement appears in multiple artifacts, merge it into one user story and list all relevant sources.

Completeness:

Cover all meaningful requirement fragments from all attached artifacts.

Do not ignore small text fragments, visual elements, diagram elements, spreadsheet rows, or technical details if they imply functionality.

Atomicity:

Each story must describe only one functionality.

Avoid combining several actions in one story.

Analyze all attached files.

Use fragments from images, screenshots, diagrams, wireframes, and spreadsheets.

Do not ignore technical requirements.

Do not go beyond the context of the provided artifacts.

If a requirement comes from a UI artifact, describe it as a UI-related user story.

If a requirement comes from an API or technical document, describe it as a system-level or integration-related user story.

If a requirement comes from a business rule, describe it as a user, administrator, or system story depending on who performs or enforces the rule.

If a requirement comes from a diagram, preserve the actor and use case relationship.

Avoid duplicate user stories.

Group related stories under clear functional sections, such as:

Public user functionality
Registration and authentication
Reservation or submission flow
Payments
Administration
Content management
Notifications
Reporting
API and integrations
System automation
Security and access control
Data management

Use only the sections that fit the provided artifacts.

Requirement: Cancellation with partial compensation

[Cancel reservation with partial fee]

• As: Customer

• I want: To cancel a reservation 12–24 hours before its start

• So that: I only pay the defined 50% cancellation fee

• Source: 20250218_222342.jpg

Requirement: API for retrieving available time slots

[Retrieve available reservation time slots]

• As: Third-party developer

• I want: To retrieve available reservation time slots through GET /api/free-slots

• So that: I can integrate availability data into an external system

• Source: Technical requirements document.docx

Requirement: PDF receipt storage

[Store payment receipts]

• As: System

• I want: To automatically store payment receipts after successful payment

• So that: Customers and administrators can download proof of payment when needed

• Source: Technical requirements document.docx

Use clear sections and avoid unnecessary explanations.

Start with:

Estimated number of expanded user stories:

Minimum:
Expected:
Maximum reasonable:

Then generate the user stories grouped by functional section.

Use this format for every story:

[Story title]

• As:

• I want:

• So that:

• Source:

After all stories are generated, include only a short final summary:

Summary:

Total generated user stories:
Main source files used:
Possible areas requiring stakeholder clarification:

Now analyze all attached artifacts and generate the user stories.
