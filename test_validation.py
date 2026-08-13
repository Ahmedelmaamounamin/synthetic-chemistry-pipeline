import pytest
from src.validation import QualityControlEngine
from src.schemas import (
    ReactionRecord, ChemicalMaterial, ChemicalRole, ExtractionProvenance,
    ExtractedQuantity, NormalizedQuantity
)

@pytest.fixture
def qc_engine():
    return QualityControlEngine()

def test_high_quality_record_passes_qc(qc_engine):
    """Test that a complete and consistent record receives a high score with no review flag."""
    text = "To a solution of aniline (93 mg, 1.0 mmol) in THF (5 mL)..."
    record = ReactionRecord(
        reaction_id="RXN-PASS",
        document_id="doc_pass",
        procedure_text=text,
        materials=[
            ChemicalMaterial(
                raw_name="aniline",
                role=ChemicalRole.SUBSTRATE,
                canonical_smiles="Nc1ccccc1",
                mw=93.13,
                mass=ExtractedQuantity(
                    raw_text="93 mg",
                    normalized=NormalizedQuantity(value=93.0, unit="mg", si_value=0.093, si_unit="g")
                ),
                moles=ExtractedQuantity(
                    raw_text="1.0 mmol",
                    normalized=NormalizedQuantity(value=1.0, unit="mmol", si_value=0.001, si_unit="mol")
                ),
                provenance=ExtractionProvenance(
                    document_id="doc_pass",
                    page_number=1,
                    exact_quote="aniline (93 mg, 1.0 mmol)"
                )
            ),
            ChemicalMaterial(
                raw_name="product X",
                role=ChemicalRole.PRODUCT,
                canonical_smiles="CC(=O)Nc1ccccc1",
                provenance=ExtractionProvenance(
                    document_id="doc_pass",
                    page_number=1,
                    exact_quote="product X"
                )
            )
        ],
        extraction_timestamp="2026-08-13T12:00:00Z",
        model_version="test_model"
    )

    metrics = qc_engine.evaluate_record(record)
    assert metrics.overall_score >= 7.0
    assert metrics.requires_human_review is False
    assert len(metrics.validation_flags) == 0

def test_stoichiometric_mismatch_flagged(qc_engine):
    """Test that mass/mole/MW inconsistencies trigger a stoichiometric mismatch flag."""
    text = "aniline (500 mg, 0.1 mmol)"  # MW 93.13: 500mg should be ~5.37 mmol, NOT 0.1 mmol!
    record = ReactionRecord(
        reaction_id="RXN-STOICH-FAIL",
        document_id="doc_fail",
        procedure_text=text,
        materials=[
            ChemicalMaterial(
                raw_name="aniline",
                role=ChemicalRole.SUBSTRATE,
                canonical_smiles="Nc1ccccc1",
                mw=93.13,
                mass=ExtractedQuantity(
                    raw_text="500 mg",
                    normalized=NormalizedQuantity(value=500.0, unit="mg", si_value=0.5, si_unit="g")
                ),
                moles=ExtractedQuantity(
                    raw_text="0.1 mmol",
                    normalized=NormalizedQuantity(value=0.1, unit="mmol", si_value=0.0001, si_unit="mol")
                ),
                provenance=ExtractionProvenance(
                    document_id="doc_fail",
                    page_number=1,
                    exact_quote="aniline (500 mg, 0.1 mmol)"
                )
            )
        ],
        extraction_timestamp="2026-08-13T12:00:00Z",
        model_version="test_model"
    )

    metrics = qc_engine.evaluate_record(record)
    assert any("STOICHIOMETRIC_MISMATCH" in flag for flag in metrics.validation_flags)
    assert metrics.requires_human_review is True

def test_hallucinated_provenance_quote_flagged(qc_engine):
    """Test that extracted quotes missing from the original procedure text get flagged."""
    text = "The mixture was stirred at 50 °C for 2 h."
    record = ReactionRecord(
        reaction_id="RXN-QUOTE-FAIL",
        document_id="doc_fail",
        procedure_text=text,
        materials=[
            ChemicalMaterial(
                raw_name="hallucinated compound",
                role=ChemicalRole.SUBSTRATE,
                provenance=ExtractionProvenance(
                    document_id="doc_fail",
                    page_number=1,
                    exact_quote="This sentence never appeared in source text"
                )
            )
        ],
        extraction_timestamp="2026-08-13T12:00:00Z",
        model_version="test_model"
    )

    metrics = qc_engine.evaluate_record(record)
    assert any("VERBATIM_QUOTE_MISMATCH" in flag for flag in metrics.validation_flags)
    assert metrics.requires_human_review is True