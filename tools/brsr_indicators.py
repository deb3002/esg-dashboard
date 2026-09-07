"""
BRSR indicator codes, and the GRI disclosures each one links to.

TWO SOURCES, kept separate on purpose:

1. INDICATOR CODES — from SEBI's BRSR format, Annexure I to circular
   SEBI/HO/CFD/CMD-2/P/CIR/2021/562 dated 10 May 2021.
   https://www.sebi.gov.in/sebi_data/commondocs/may-2021/Business%20responsibility%20and%20sustainability%20reporting%20by%20listed%20entitiesAnnexure1_p.PDF

   The ESG portal's row titles follow SEBI's numbered questions in the same
   order, so each row is matched to its indicator by position and wording.

2. GRI DISCLOSURES — from "Linking the GRI Standards and the SEBI BRSR
   Framework", GRI with BSE, 2022.
   https://www.globalreporting.org/media/ioqnxtmx/sebi_brsb_gri_linkage_doc.pdf

   Its summary table gives the GRI disclosures for each BRSR indicator.

WHERE A ROW IS NOT LISTED HERE it keeps the principle-level GRI mapping.
That is a deliberate fallback, not an oversight: a row whose indicator could
not be identified with confidence gets the coarser, still-sourced answer
rather than a precise-looking guess.

Rows added by the 2023 BRSR Core circular (assurance, and the nine Core
attributes) have no entry in the 2022 linkage document. They carry an
indicator code but no indicator-level GRI.
"""

import re

# Subfactor title -> BRSR indicator code.
INDICATOR_CODES = {
    # ---- Section A: General Disclosures ----
    "CIN": "A1",
    "Name of the Listed Entity": "A2",
    "Year of Incorporation": "A3",
    "Registered Office Address": "A4",
    "Corporate Address": "A5",
    "E-mail": "A6",
    "Telephone": "A7",
    "Website": "A8",
    "Financial Year": "A9",
    "Listing Stock Exchange(s)": "A10",
    "Paid-up Capital": "A11",
    "Contact Details": "A12",
    "Reporting Boundary": "A13",
    "Assurance Provider": "A-Assurance",
    "Types of Assurance": "A-Assurance",
    "Business Activities": "A14",
    "Products and Services": "A15",
    "Plants and Office Location": "A16",
    "Geographical Presence and Customer Overview": "A17",
    "Employees and Workers": "A18",
    "Women Employee Inclusion": "A19",
    "Employee Turnover Rate": "A20",
    "Holdings, Subsidiaries and Associate Companies": "A21",
    "CSR Details": "A22",
    "Regulatory Compliances": "A23",
    "Business Material Issues": "A24",

    # ---- Section B: Management and Process Disclosures ----
    "Policies and Management Processes": "B1",
    "Implementation of Policies into Procedures": "B2",
    "Policies Extended to Value Chain Partners": "B3",
    "Mapped Standards and Principles": "B4",
    "Commitments and Goals": "B5",
    "Reconciliation of Commitments and Goals": "B6",
    "Director’s Statement": "B7",
    "Oversight and Responsibilities of Business Responsibility Policies": "B8",
    "Sustainability Committee": "B9",
    "NGRBC Review": "B10",
    "Independent Assessment of Policies": "B11",
    "Principles Not Covered in Company Policies": "B12",

    # ---- Principle 1 ----
    "Training and Awareness Programs": "P1-E1",
    "Fines and Penalties Paid": "P1-E2",
    "Appeal or Revision in Regulatory Proceedings": "P1-E3",
    "Anti-Corruption/ Anti-Bribery Policy": "P1-E4",
    "Disciplinary Actions": "P1-E5",
    "Complaints of Conflict of Interests": "P1-E6",
    "Action Against Corruption and Conflicts of Interests": "P1-E7",
    "Accounts Payables Days": "P1-Core",
    "Openness of business": "P1-Core",
    "Awareness Programs for Value Chain Partners": "P1-L1",
    "Mechanism to Avoid Conflict of Interests": "P1-L2",

    # ---- Principle 2 ----
    "R&D and Technology Expenditure": "P2-E1",
    "Sustainable Sourcing": "P2-E2",
    "Products Reuse, Recycling and Disposal": "P2-E3",
    "Extended Producer Responsibility": "P2-E4",
    "Life Cycle Assessments": "P2-L1",
    "Harmful Waste and Product Disposal Strategy": "P2-L2",
    "Recycled and Reused Raw Material": "P2-L3",
    "Reuse, Recycling and Dispose Own Products and Packaging Materials": "P2-L4",
    "Reclaimed Products and Packaging Materials": "P2-L5",

    # ---- Principle 3 ----
    "Employees Well-being": "P3-E1a",
    "Workers Well-being": "P3-E1b",
    "Employees and Workers Well-being Spending": "P3-Core",
    "Retirement Benefits": "P3-E2",
    "Accessibility of Workplaces": "P3-E3",
    "Equal Opportunity at Workplace": "P3-E4",
    "Return to Work and Retention Rates": "P3-E5",
    "Mechanism to Receive and Redress Grievances": "P3-E6",
    "Employees and Workers Membership with Associations or Unions": "P3-E7",
    "Employees and Workers Training": "P3-E8",
    "Annual Performance Reviews": "P3-E9",
    "Health and Safety Management System": "P3-E10",
    "Safety Related Incidents": "P3-E11",
    "Measures of Health and Safety": "P3-E12",
    "Complaints Regarding Working Conditions and Health & Safety": "P3-E13",
    "Assessments of Working Conditions and Health & Safety Practices": "P3-E14",
    "Corrective Action to Address Safety Related Incidents": "P3-E15",
    "Insurance Coverage for Employees and Workers": "P3-L1",
    "Provisions for Statutory Dues by Value Chain Partners": "P3-L2",
    "Employee and Family Rehabilitation": "P3-L3",
    "Post Employment Career Assistance": "P3-L4",
    "Assessment of Value Chain Partners": "P3-L5",
    "Health & Safety Practices of Value Chain Partners": "P3-L6",

    # ---- Principle 4 ----
    "Identify Key Stakeholder Groups": "P4-E1",
    "Key Stakeholders and Engagement": "P4-E2",
    "Process of Soliciting Stakeholder Feedback": "P4-L1",
    "Use of Stakeholder Feedback": "P4-L2",
    "Addressing Stakeholder Concerns": "P4-L3",

    # ---- Principle 5 ----
    "Employee Training for Human Rights": "P5-E1",
    "Minimum Wages Paid": "P5-E2",
    "Median Remuneration / Wages": "P5-E3",
    "Median Remuneration / Wages to Females": "P5-Core",
    "Dedicated Person for Reporting Human Rights Issues": "P5-E4",
    "Grievance Redressal Mechanism for Human Rights Issues": "P5-E5",
    "Employee Complaints": "P5-E6",
    "Complaints on POSH": "P5-Core",
    "Preventing Discrimination and Harassment": "P5-E7",
    "Inclusion of Human Rights in Agreements": "P5-E8",
    "Assessments of Workplace for Labor Practices": "P5-E9",
    "Actions Against Adverse Work Conditions": "P5-E10",
    "Addressing Human Rights Grievances": "P5-L1",
    "Scope of Human Rights Due-Diligence": "P5-L2",
    "Workplace Accessibility for the Differently Abled": "P5-L3",
    "Value Chain Partner Human Rights Compliance": "P5-L4",
    "Human Rights Compliant Value Chain Partners": "P5-L5",

    # ---- Principle 6 ----
    "Energy Consumption": "P6-E1",
    "Projects under Performance, Achieve and Trade": "P6-E2",
    "Water Usage": "P6-E3",
    "Water Discharge": "P6-L2",
    "Zero Liquid Discharge Mechanism": "P6-E4",
    "Air Emissions Other Than GHG": "P6-E5",
    "Amount of GHG Emission (Scope 1 and 2)": "P6-E6",
    "GHG Emission Reduction Initiatives": "P6-E7",
    "Waste Management Assessment": "P6-E8",
    "Waste Management Strategy": "P6-E9",
    "Projects Around Ecologically Sensitive Areas": "P6-E10",
    "Environmental Impact Assessments": "P6-E11",
    "Compliance with Environmental Regulations": "P6-E12",
    "Water Stress Management": "P6-L3",
    "Amount of GHG Emission (Scope 3)": "P6-L4",
    "Protect Nature and Biodiversity": "P6-L5",
    "Resource Efficiency and Innovation": "P6-L6",
    "Disaster Management": "P6-L7",
    "Value Chain Environment Risk Management": "P6-L8",
    "Environment Responsible Value Chain Partners": "P6-L9",
    "Green Credits Generated or Procured": "P6-Core",

    # ---- Principle 7 ----
    "Affiliations with Trade and Industry Chambers": "P7-E1",
    "Anti-Competitive Practices": "P7-E2",
    "Public Policy Positions": "P7-L1",

    # ---- Principle 8 ----
    "Social Impact Assessments": "P8-E1",
    "Rehabilitation and Resettlement": "P8-E2",
    "Community Grievance Redressal Mechanism": "P8-E3",
    "Local Sourcing and Community Support": "P8-E4",
    "Wages Paid for Job Creation": "P8-Core",
    "Actions Based on Social Impact Assessments": "P8-L1",
    "CSR Activities": "P8-L2",
    "Community Support Through Sourcing of Materials": "P8-L3",
    "Intellectual Properties and Benefits": "P8-L4",
    "Intellectual Property Related Disputes and Corrective Actions": "P8-L5",
    "CSR Project Beneficiaries": "P8-L6",

    # ---- Principle 9 ----
    "Consumer Complaints and Feedback Collection Mechanisms": "P9-E1",
    "Sustainable Products and Services": "P9-E2",
    "Consumer Complaints": "P9-E3",
    "Product Safety Recalls": "P9-E4",
    "Cyber Security and Data Privacy Policy": "P9-E5",
    "Cyber Security Breach and Corrective Action": "P9-E6",
    "Data Breaches": "P9-L5",
    "Product Details": "P9-L1",
    "Customer Education and Awareness": "P9-L2",
    "Customer Communication": "P9-L3",
    "Product Details and Satisfaction Survey": "P9-L4",
}


# BRSR indicator code -> GRI disclosures, transcribed from the linkage
# document's summary table. Absent = no entry there, or the indicator
# postdates the 2022 document.
GRI_BY_INDICATOR = {
    # Section A
    "A2":  "GRI 2-1-a",
    "A5":  "GRI 2-1-c",
    "A6":  "GRI 2-3-d",
    "A7":  "GRI 2-3-d",
    "A9":  "GRI 2-3-a, 2-3-b",
    "A12": "GRI 2-3-d",
    "A13": "GRI 2-2-a, 2-2-c",
    "A14": "GRI 2-6-b-i",
    "A15": "GRI 2-6-b-i",
    "A16": "GRI 2-6-b-i",
    "A17": "GRI 2-6-b-i, 2-6-b-iii",
    "A18": "GRI 2-7-a, 2-7-b-i-ii, 2-8-a, 405-1-b-iii",
    "A19": "GRI 405-1-a-i, 405-1-b-i",
    "A20": "GRI 401-1-b",
    "A21": "GRI 2-2-a, 2-2-b",
    "A22": "GRI 201-1-a-i-ii",
    "A23": "GRI 2-25-e",
    "A24": "GRI 3-1-a-i-ii, 3-1-b, 3-2-a, 3-3-a, 3-3-d-i-ii",

    # Section B
    "B1":  "GRI 2-23-a, 2-23-c, 2-23-d",
    "B2":  "GRI 2-24-a-ii",
    "B3":  "GRI 2-23-e",
    "B5":  "GRI 3-3-c, 3-3-e-ii",
    "B6":  "GRI 3-3-e-iii",
    "B7":  "GRI 2-22-a",
    "B8":  "GRI 2-13-a-i",
    "B9":  "GRI 2-9-b, 2-9-c-i-viii",
    "B11": "GRI 2-5-b-i-iii",

    # Principle 1
    "P1-E1": "GRI 2-17-a, 2-24-a-iv",
    "P1-E2": "GRI 2-27-a-i-ii, 2-27-b-i-ii, 2-27-c, 2-27-d",
    "P1-E3": "GRI 2-27-a-i-ii",
    "P1-E5": "GRI 205-3-a, 205-3-b",
    "P1-E6": "GRI 2-25-e",
    "P1-E7": "GRI 205-3-d",
    "P1-L1": "GRI 2-24-a-iv",
    "P1-L2": "GRI 2-10-b-iii, 2-15-a",

    # Principle 2
    "P2-E2": "GRI 3-3-d, GRI 306-2-a, GRI 301",
    "P2-E3": "GRI 308-1-a, GRI 414-1-a",
    "P2-L2": "GRI 3-3-a, 3-3-d-i-iii, GRI 306-2-a",
    "P2-L3": "GRI 301-2-a",
    "P2-L5": "GRI 301-3-a",

    # Principle 3
    "P3-E1a": "GRI 401-2-a-i-vii",
    "P3-E2":  "GRI 201-3-b-i-iii, 201-3-c, 201-3-d, 201-3-e",
    "P3-E5":  "GRI 401-3-a, 401-3-b, 401-3-c, 401-3-d, 401-3-e",
    "P3-E6":  "GRI 2-25-b",
    "P3-E7":  "GRI 2-30-a",
    "P3-E8":  "GRI 403-5-a, GRI 404-1-a-i, 404-2-a",
    "P3-E9":  "GRI 404-3-a",
    "P3-E10": "GRI 403-1-a, 403-1-b, 403-2-a, 403-2-b, 403-2-c, 403-6-a",
    "P3-E11": "GRI 403-9-a-i-v, 403-9-b-i-v, 403-10-a, 403-10-b-ii",
    "P3-E12": "GRI 3-3-d-i-iii, GRI 403-2-a-i-ii, 403-9-c-iii, 403-9-d, 403-10-c-iii",
    "P3-E13": "GRI 2-25-e",
    "P3-E14": "GRI 3-3-e-i, GRI 403",
    "P3-E15": "GRI 3-3-d-i-ii, GRI 403-9-c-ii-iii, 403-9-d, 403-10-c-ii-iii",
    "P3-L3":  "GRI 3-3-d-ii, GRI 403",
    "P3-L4":  "GRI 404-2-b",
    "P3-L5":  "GRI 414-2-a",
    "P3-L6":  "GRI 414-2-d, 414-2-e",

    # Principle 4
    "P4-E1": "GRI 2-29-a-i",
    "P4-E2": "GRI 3-1-b, GRI 2-29-a-i-iii",
    "P4-L1": "GRI 2-29-a-i",
    "P4-L2": "GRI 3-1-a-i-ii, 3-1-b",
    "P4-L3": "GRI 2-29-a-i-iii",

    # Principle 5
    "P5-E1": "GRI 2-24-a-iv, GRI 205-2-e, GRI 403-5-a, GRI 404-1-a-i-ii, GRI 410-1-a",
    "P5-E2": "GRI 202-1-a, 202-1-b",
    "P5-E3": "GRI 405-2-a, GRI 2-19-a-i-v, 2-21-a",
    "P5-E4": "GRI 2-13-a-i-ii",
    "P5-E5": "GRI 2-25-b, 2-25-d, 2-25-e",
    "P5-E6": "GRI 406-1-a, GRI 2-25-e",
    "P5-E7": "GRI 2-25-e",
    "P5-E8": "GRI 2-23-a-iv, 2-23-e, 2-23-f, 2-24-a-iii, GRI 414",
    "P5-E10": "GRI 3-3-d-i-ii",
    "P5-L1": "GRI 2-25-b, 2-25-e, GRI 3-3-d-i-ii",
    "P5-L2": "GRI 3-1-a-i, 3-3-a, 3-3-c, 3-3-d",
    "P5-L4": "GRI 414-1-a, 414-2-a",
    "P5-L5": "GRI 414-2-d, 414-2-e",

    # Principle 6
    "P6-E1":  "GRI 302-1-a, 302-1-b, 302-1-c-i, 302-1-e, 302-3-a",
    "P6-E2":  "GRI 3-3, GRI 302",
    "P6-E3":  "GRI 303-3-a-i-v, 303-5-a, 303-1-a, 303-2-a",
    "P6-E5":  "GRI 305-7-a-i-vii",
    "P6-E6":  "GRI 305-1-a, 305-1-b, 305-2-a, 305-2-b, 305-2-c, 305-4-a, 305-4-b, 305-4-c",
    "P6-E7":  "GRI 305-5-a, 305-5-b, 305-5-c, 305-5-d",
    "P6-E8":  "GRI 306-3-a, 306-4-a, 306-4-b-i-iii, 306-4-c-i-iii, 306-5-a, 306-5-b-i-iii, 306-5-c-i-iv",
    "P6-E9":  "GRI 306-2-a, GRI 3-3-c, 3-3-d-i-ii",
    "P6-E10": "GRI 304-1-a-i-v",
    "P6-E11": "GRI 304, GRI 413-1-a-ii, GRI 303-1-a",
    "P6-E12": "GRI 2-27-a-i-ii, 2-27-b-i-ii",
    "P6-L1":  "GRI 302-1-a, 302-1-b, 302-1-c-i, 302-1-e",
    "P6-L2":  "GRI 303-4-a-i-iv",
    "P6-L3":  "GRI 303-3-b-i-iv, 303-4-a-i-ii",
    "P6-L4":  "GRI 305-3-a, 305-3-b, 305-4-a, 305-4-b, 305-4-c",
    "P6-L5":  "GRI 304-2-a-i-vi, 304-2-b-i-iv, 304-3-a",
    "P6-L6":  "GRI 3-3, GRI 301, 302, 303, 304, 305, 306",
    "P6-L7":  "GRI 2-28-a",
    "P6-L8":  "GRI 308-2-c, 308-2-d",
    "P6-L9":  "GRI 308-1-a, 308-2-a",

    # Principle 7
    "P7-E2": "GRI 3-3, GRI 206",
    "P7-L1": "GRI 2-28-a, GRI 415",

    # Principle 8
    "P8-E1": "GRI 413-1-a-i-iii",
    "P8-E2": "GRI 413-1-a-iv",
    "P8-E3": "GRI 2-25-b, 2-25-d, 2-25-e",
    "P8-E4": "GRI 204-1-a, 204-1-b, 204-1-c",
    "P8-L1": "GRI 413-1-a-iv, GRI 3-3-d-i-ii",
    "P8-L2": "GRI 413-1-a-iv",
    "P8-L3": "GRI 3-3, GRI 204-1-a",
    "P8-L4": "GRI 201-1-a",
    "P8-L6": "GRI 413-1-a-iv",

    # Principle 9
    "P9-E2": "GRI 417-1-a-i-v, 417-1-b",
    "P9-E3": "GRI 418-1-a-i-ii, 418-1-b",
    "P9-E4": "GRI 416-2-a-i-iii",
    "P9-E5": "GRI 3-3, GRI 418, GRI 2-23-a, 2-23-c",
    "P9-E6": "GRI 3-3-d-i-ii",
    "P9-L1": "GRI 2-6-b-i",
    "P9-L2": "GRI 3-3, GRI 417",
    "P9-L4": "GRI 417-1-a-i-v, 417-1-b",
    "P9-L5": "GRI 418-1-a",
}

INDICATOR_CODES = {re.sub(r"\s+", " ", k.replace("\u00a0", " ")).strip(): v
                   for k, v in INDICATOR_CODES.items()}

# --------------------------------------------------------------------------
# GRI series -> IFC Performance Standard
# --------------------------------------------------------------------------
#
# WEAKER THAN THE MAPPINGS ABOVE. Read this before trusting it.
#
# Source: IFC, "Elevating Environmental, Social, and Governance Reporting in
# Emerging Markets — Aligning IFC Disclosure Requirements with Other
# International Standards", January 2025, and its companion benchmarking
# analysis.
#   https://www.ifc.org/content/dam/ifc/doc/2025/elevating-esg-reporting-in-emerging-markets.pdf
#   https://www.ifcbeyondthebalancesheet.org/sites/default/files/2025-01/IFC%20ESG%20Benchmarking%20Analysis_0.pdf
#
# Three caveats, all material:
#
# 1. That work is an ALIGNMENT ASSESSMENT, not a crosswalk. It rates IFC
#    Performance Standards against GRI at series level — "IFC PSs have strong
#    alignment with some Environment (GRI 300s) and Social (GRI 400s) topics"
#    — rather than mapping GRI 303-3 to a specific Performance Standard.
#
# 2. The BRSR-to-IFC link is therefore CHAINED: BRSR indicator -> GRI
#    disclosure -> IFC PS. No published document asserts that composition.
#    The first hop is official; the second is an alignment rating; the join
#    is inference.
#
# 3. GRI 200-series (Economic Performance) is deliberately excluded — the
#    same source rates its alignment with IFC as weak.
#
# IFC tags are therefore marked unverified and render differently from the
# sourced BRSR and GRI tags. Do not promote them to verified without a real
# crosswalk.

IFC_BY_GRI_SERIES = {
    # Environmental — GRI 300s
    "301": "PS3",   # Materials
    "302": "PS3",   # Energy
    "303": "PS3",   # Water and Effluents
    "304": "PS6",   # Biodiversity
    "305": "PS3",   # Emissions
    "306": "PS3",   # Waste
    "308": "PS1",   # Supplier Environmental Assessment (risk management)

    # Social — GRI 400s
    "401": "PS2",   # Employment
    "402": "PS2",   # Labor/Management Relations
    "403": "PS2",   # Occupational Health and Safety
    "404": "PS2",   # Training and Education
    "405": "PS2",   # Diversity and Equal Opportunity
    "406": "PS2",   # Non-discrimination
    "407": "PS2",   # Freedom of Association
    "408": "PS2",   # Child Labor
    "409": "PS2",   # Forced or Compulsory Labor
    "410": "PS4",   # Security Practices
    "411": "PS7",   # Rights of Indigenous Peoples
    "413": "PS4",   # Local Communities
    "414": "PS1",   # Supplier Social Assessment (risk management)

    # GRI 2 (General Disclosures) and GRI 3 (Material Topics) are NOT mapped.
    # They do align with PS1's management-system requirements in the abstract,
    # but applying that put the company's e-mail address, telephone number and
    # registered office under "Assessment and Management of Environmental and
    # Social Risks" — 26 Section A admin rows in a 74-row bucket. Coverage is
    # not worth a mapping that reads as nonsense. Dropped 7 Sep 2026.
}

IFC_NAMES = {
    "PS1": "Assessment and Management of E&S Risks",
    "PS2": "Labor and Working Conditions",
    "PS3": "Resource Efficiency and Pollution Prevention",
    "PS4": "Community Health, Safety and Security",
    "PS5": "Land Acquisition and Involuntary Resettlement",
    "PS6": "Biodiversity Conservation",
    "PS7": "Indigenous Peoples",
    "PS8": "Cultural Heritage",
}

IFC_SOURCE = ("Derived by alignment from IFC's GRI benchmarking "
              "(IFC, January 2025) — not a published BRSR-to-IFC mapping")

SEBI_SOURCE = ("SEBI BRSR format, Annexure I to circular "
               "SEBI/HO/CFD/CMD-2/P/CIR/2021/562, 10 May 2021")
