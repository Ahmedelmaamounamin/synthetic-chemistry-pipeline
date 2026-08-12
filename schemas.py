from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, FieldValidationInfo, field_validator


class ChemicalRole(str, Enum):
    SUBSTRATE = "substrate"
    REACTANT = "reactant"
    REAGENT = "reagent"
    CATALYST = "catalyst"
    LIGAND = "ligand"
    SOLVENT = "solvent"
    BASE = "base"
    ACID = "acid"
    ADDITIVE = "additive"
    REDUCING_AGENT = "reducing_agent"
    OXIDIZING_AGENT = "oxidizing_agent"
    PROTECTING_GROUP = "protecting_group"
    COUPLING_PARTNER = "coupling_partner"
    QUENCH_AGENT = "quench_agent"
    WORKUP_AGENT = "workup_agent"
    DRYING_AGENT = "drying_agent"
    PRODUCT = "product"
    BYPRODUCT = "byproduct"
    UNKNOWN = "unknown"


class ExtractionProvenance(BaseModel):
    document_id: str
    page_number: int
    exact_quote: str = Field(description="The verbatim text span extracted from the source document.")
    char_start: Optional[int] = None
    char_end: Optional[int] = None


class NormalizedQuantity(BaseModel):
    value: float
    unit: str
    si_value: float = Field(description="Normalized value in SI base units (e.g., grams, moles, Kelvin, seconds).")
    si_unit: str


class ExtractedQuantity(BaseModel):
    raw_text: str = Field(description="Exact text string representing the quantity, e.g., '500 mg'.")
    normalized: Optional[NormalizedQuantity] = None
    provenance: Optional[ExtractionProvenance] = None


class ChemicalMaterial(BaseModel):
    raw_name: str = Field(description="Raw name of the compound as written in the text.")
    role: ChemicalRole = Field(default=ChemicalRole.UNKNOWN)
    is_limiting: bool = Field(default=False, description="True if this material is designated as the limiting reagent.")

    # Structure details (populated during normalization phase)
    smiles: Optional[str] = None
    canonical_smiles: Optional[str] = None
    inchi_key: Optional[str] = None
    formula: Optional[str] = None
    mw: Optional[float] = None
    structure_source: Optional[str] = Field(default=None, description="OPSIN, PubChem, LLM_Inferred, or Unresolved")

    # Quantities
    mass: Optional[ExtractedQuantity] = None
    volume: Optional[ExtractedQuantity] = None
    moles: Optional[ExtractedQuantity] = None
    equivalents: Optional[ExtractedQuantity] = None
    concentration: Optional[ExtractedQuantity] = None

    provenance: ExtractionProvenance


class ReactionConditions(BaseModel):
    temperature_raw: Optional[str] = None
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    time_raw: Optional[str] = None
    time_hours: Optional[float] = None
    atmosphere: Optional[str] = Field(default=None, description="e.g., Nitrogen, Argon, Air, Vacuum")
    pressure_raw: Optional[str] = None
    reflux: bool = False
    stirring_speed: Optional[str] = None
    provenance: Optional[ExtractionProvenance] = None


class ReactionYield(BaseModel):
    raw_text: str
    value_percent: Optional[float] = None
    yield_type: str = Field(default="isolated", description="isolated, determined_by_nmr, crude, or calculated")
    provenance: Optional[ExtractionProvenance] = None


class WorkupStep(BaseModel):
    step_number: int
    action_type: str = Field(description="e.g., extraction, washing, drying, filtration, concentration, quench")
    reagents_used: List[str] = Field(default_factory=list)
    solvents_used: List[str] = Field(default_factory=list)
    raw_description: str
    provenance: Optional[ExtractionProvenance] = None


class PurificationStep(BaseModel):
    method: str = Field(description="e.g., silica_gel_chromatography, recrystallization, distillation, trituration")
    eluent_system: Optional[str] = None
    stationary_phase: Optional[str] = None
    raw_description: str
    provenance: Optional[ExtractionProvenance] = None


class QualityMetrics(BaseModel):
    provenance_completeness: float = Field(ge=0.0, le=10.0)
    chemical_validity: float = Field(ge=0.0, le=10.0)
    stoichiometric_consistency: float = Field(ge=0.0, le=10.0)
    overall_score: float = Field(ge=0.0, le=10.0)
    validation_flags: List[str] = Field(default_factory=list)
    requires_human_review: bool = False


class ReactionRecord(BaseModel):
    reaction_id: str
    document_id: str
    title: Optional[str] = None
    procedure_text: str

    # Reaction Entities
    materials: List[ChemicalMaterial] = Field(default_factory=list)
    conditions: ReactionConditions = Field(default_factory=ReactionConditions)
    workup: List[WorkupStep] = Field(default_factory=list)
    purification: List[PurificationStep] = Field(default_factory=list)
    yield_info: Optional[ReactionYield] = None

    # Generated Representations
    reaction_smiles: Optional[str] = None
    is_atom_mapped: bool = False

    # Metadata and QC
    quality: Optional[QualityMetrics] = None
    extraction_timestamp: str
    model_version: str