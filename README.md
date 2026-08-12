# Synthetic Chemistry Reaction Extraction & Normalization Pipeline

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![RDKit](https://img.shields.io/badge/cheminformatics-RDKit-green.svg)](https://www.rdkit.org/)
[![Pydantic v2](https://img.shields.io/badge/data_validation-Pydantic_v2-red.svg)](https://docs.pydantic.dev/)
[![OpenRouter Ready](https://img.shields.io/badge/LLM-OpenRouter-purple.svg)](https://openrouter.ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An audit-ready, production-grade Python pipeline designed to extract, normalize, and validate structured synthetic chemistry records from unstructured literature (PDFs and patents).

This platform combines **generative LLM extraction** via [Instructor](https://github.com/jxnl/instructor) (supporting OpenRouter, local, and commercial LLMs) with **deterministic cheminformatics & unit normalization engines** (RDKit, OPSIN, PubChem API, Pint).

---

## Key Features

* **Multi-Pass Structured Extraction:** Isolates experimental procedures from literature and extracts chemical materials, roles, reaction conditions, workup steps, purification, and isolated yields into a strict Pydantic v2 schema.
* **OpenRouter Integration:** Flexible backend support for free open-weights models (`meta-llama/llama-3.3-70b-instruct:free`, `google/gemini-2.0-flash-lite-001:free`), local vLLM instances, or OpenAI endpoints.
* **Deterministic Unit Normalization:** Converts reported masses, volumes, temperatures, times, and concentrations into standardized SI bases using `Pint` without relying on LLM arithmetic.
* **Name-to-Structure Resolution:** Resolves IUPAC and trivial compound names into Canonical SMILES, InChIKeys, Molecular Formulas, and Exact Molecular Weights using a cascading fallback mechanism:
  $$\text{OPSIN (IUPAC Parser)} \longrightarrow \text{PubChem PUG-REST API} \longrightarrow \text{RDKit Descriptor Validation}$$
* **First-Class Provenance Tracking:** Every extracted entity retains exact source metadata (document ID, page number, verbatim text quote, character offsets).
* **Deterministic Quality Control Engine:** Automatically grades each extracted reaction record across four dimensions (Provenance, Chemical Validity, Stoichiometric Consistency, Text Verification) on a $0.0 - 10.0$ scale.
* **Human-in-the-Loop Routing:** Automatically routes records with low QC scores ($< 7.0$) or stoichiometric mismatches to a human review queue instead of poisoning down-stream ML datasets.

---

## Pipeline Architecture

```
                              UNSTRUCTURED PDF LITERATURE
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │     Stage A: PDF Ingestion      │
                          │ (PyMuPDF / Character Offsets)   │
                          └────────────────┬────────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │  Stage B: Procedure Detection   │
                          │ (Regex Boundary & Keyword Rules)│
                          └────────────────┬────────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │ Stage C: Multi-Pass Extraction  │
                          │  (Instructor + OpenRouter API)  │
                          └────────────────┬────────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │ Stage D: Deterministic Engine   │
                          │ - Structure: OPSIN/PubChem/RDKit│
                          │ - Units: Pint SI Normalization  │
                          └────────────────┬────────────────┘
                                           │
                                           ▼
                          ┌─────────────────────────────────┐
                          │ Stage E: Quality Control Check  │
                          │ (Stoichiometry / Text Provenance)│
                          └────────────────┬────────────────┘
                                           │
                   ┌───────────────────────┴───────────────────────┐
                   │                                               │
                   ▼                                               ▼
      ┌─────────────────────────┐                     ┌─────────────────────────┐
      │     QC Score ≥ 7.0      │                     │      QC Score < 7.0     │
      │ Approved & Persisted to │                     │ Routed to Human Review  │
      │   SQLite & JSONL DB     │                     │     Queue (Review = 1)  │
      └─────────────────────────┘                     └─────────────────────────┘
```
---

## Project Directory Structure

```text
synthetic-chemistry-pipeline/
├── materials/                      # Raw PDF input files
├── output/                         # Processed SQLite database and JSONL logs
├── cache/                          # Intermediate parsing caches
├── src/
│   ├── __init__.py
│   ├── config.py                   # Paths, OpenRouter, and pipeline settings
│   ├── schemas.py                  # Pydantic data models & provenance schemas
│   ├── ingestion.py                # PyMuPDF ingestion & offset extraction
│   ├── chunking.py                 # Structural section & experimental detector
│   ├── extraction.py               # Instructor + OpenRouter extraction engine
│   ├── normalization.py            # Pint physical quantity normalizer
│   ├── chemistry.py                # RDKit, OPSIN, and PubChem resolver
│   ├── validation.py               # Deterministic QC & stoichiometric engine
│   ├── database.py                 # SQLite/JSONL relational persistence layer
│   └── pipeline.py                 # Main execution workflow script
├── tests/
│   ├── test_chemistry.py
│   ├── test_extraction.py
│   └── test_validation.py
├── .env.example                    # Template for environment variables
├── .gitignore
├── requirements.txt
└── README.md

```
# Installation & Setup
## Prerequisites
* Python 3.10+
* Operating System: Windows 10/11, Linux, or macOS

## 1. Clone the Repository
```
git clone [https://github.com/your-username/synthetic-chemistry-pipeline.git](https://github.com/your-username/synthetic-chemistry-pipeline.git)
cd synthetic-chemistry-pipeline
```
## 2. Set Up Virtual Environment
On Windows (PowerShell):
```
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On Linux / macOS:
```
python3 -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies
```
pip install --upgrade pip
pip install -r requirements.txt
```
requirements.txt
```
rdkit>=2023.9.1
pydantic>=2.5.0
instructor>=1.0.0
openai>=1.10.0
pymupdf>=1.23.0
pdfplumber>=0.10.0
pint>=0.23
requests>=2.31.0
pandas>=2.0.0
```

# Environment & Configuration
Create a .env file in the project root directory (or edit src/config.py):
```
# Copy example template
cp .env.example .env
```

Set your OpenRouter API key:
```
OPENROUTER_API_KEY=sk-or-v1-YOUR_ACTUAL_API_KEY
```
To set the environment variable in Windows PowerShell for the current session:
```
$env:OPENROUTER_API_KEY="sk-or-v1-YOUR_ACTUAL_API_KEY"
```

Model Selection (src/config.py)
You can switch models freely in src/config.py:
```
# Recommended Free OpenRouter Models:
# - "meta-llama/llama-3.3-70b-instruct:free" (High performance, excellent schema compliance)
# - "google/gemini-2.0-flash-lite-001:free" (Fast, high context window)
# - "openrouter/auto"                        (Automatic routing)
extraction_model: str = "meta-llama/llama-3.3-70b-instruct:free"
```

# Usage
## 1. Place Source PDFs
Place your target literature PDFs inside the materials input directory:

materials_dir in src/config.py

## 2. Run the Processing Pipeline
```
python -m src.pipeline
```
## 3. Pipeline Output
* SQLite Database: Saved at output/reactions.db with structured relational tables for reactions and materials.
* JSON Schema Outputs: Audit-ready nested JSON files stored with full metadata and quality flags.

# Quality Control (QC) Scoring Matrix

Every record is evaluated deterministically using four weighted metrics (0.0–10.0 scale):

QC Score = 0.25(Provenance) + 0.35(Chemical Validity) + 0.25(Stoichiometry) + 0.15(Text Match)


| Metric | Weight | Evaluation Criteria |
|---|---:|---|
| **Provenance Completeness** | 25% | Checks if extracted entities have non-empty verbatim source text quotes attached. |
| **Chemical Validity** | 35% | Verifies presence of reactant/substrate and product, valid SMILES parsing, and IUPAC name resolution ratio. |
| **Stoichiometric Consistency** | 25% | Checks for physical consistency across reported Mass, Molecular Weight, and Moles (Mass ≈ MW × Moles). |
| **Text Support Verification** | 15% | Ensures verbatim quotes actually exist within the source PDF text block. |

## Data Schema Example

```
{
  "reaction_id": "RXN-C3A9B1D2",
  "document_id": "journal_chem_2024_001",
  "procedure_text": "To a solution of compound 1 (500 mg, 2.1 mmol) in THF (10 mL)...",
  "materials": [
    {
      "raw_name": "compound 1",
      "role": "substrate",
      "is_limiting": true,
      "canonical_smiles": null,
      "mass": {
        "raw_text": "500 mg",
        "normalized": { "value": 500.0, "unit": "mg", "si_value": 0.5, "si_unit": "g" }
      },
      "moles": {
        "raw_text": "2.1 mmol",
        "normalized": { "value": 2.1, "unit": "mmol", "si_value": 0.0021, "si_unit": "mol" }
      },
      "provenance": {
        "document_id": "journal_chem_2024_001",
        "page_number": 3,
        "exact_quote": "compound 1 (500 mg, 2.1 mmol)"
      }
    }
  ],
  "conditions": {
    "temperature_raw": "80 °C",
    "temperature_min_c": 80.0,
    "time_raw": "4 h",
    "time_hours": 4.0,
    "atmosphere": "Nitrogen"
  },
  "yield_info": {
    "raw_text": "81% yield",
    "value_percent": 81.0,
    "yield_type": "isolated"
  },
  "quality": {
    "provenance_completeness": 10.0,
    "chemical_validity": 8.5,
    "stoichiometric_consistency": 10.0,
    "overall_score": 9.2,
    "validation_flags": [],
    "requires_human_review": false
  }
}
```

## Development & Testing
### Run unit tests to verify RDKit structure validation, unit normalization, and quality scoring engines:
```
pytest tests/
```
