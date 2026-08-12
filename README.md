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

