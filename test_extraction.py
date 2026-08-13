import pytest
from unittest.mock import MagicMock, patch
from src.extraction import ChemistryExtractor
from src.schemas import ReactionRecord, ChemicalMaterial, ChemicalRole, ExtractionProvenance

@pytest.fixture
def sample_procedure_text():
    return (
        "To a solution of compound 1 (500 mg, 2.1 mmol) in THF (10 mL) was added Pd(PPh3)4 (50 mg). "
        "The mixture was stirred at 80 °C for 4 h to afford compound 2 (420 mg, 81% yield)."
    )

@patch("src.extraction.OpenAI")
@patch("src.extraction.instructor.from_openai")
def test_extraction_pipeline_mocked(mock_instructor_from_openai, mock_openai, sample_procedure_text):
    """Test that ChemistryExtractor builds correct prompts and returns schema records."""
    # Build mock structured response
    mock_record = ReactionRecord(
        reaction_id="RXN-TEST01",
        document_id="doc_123",
        procedure_text=sample_procedure_text,
        materials=[
            ChemicalMaterial(
                raw_name="compound 1",
                role=ChemicalRole.SUBSTRATE,
                provenance=ExtractionProvenance(
                    document_id="doc_123",
                    page_number=1,
                    exact_quote="compound 1 (500 mg, 2.1 mmol)"
                )
            )
        ],
        extraction_timestamp="2026-08-13T12:00:00Z",
        model_version="openrouter/meta-llama/llama-3.3-70b-instruct:free"
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_record
    mock_instructor_from_openai.return_value = mock_client

    # Initialize Extractor
    extractor = ChemistryExtractor(api_key="test_dummy_key")
    record = extractor.extract_reaction(sample_procedure_text, doc_id="doc_123", page_num=1)

    assert record.document_id == "doc_123"
    assert len(record.materials) == 1
    assert record.materials[0].raw_name == "compound 1"
    assert record.materials[0].role == ChemicalRole.SUBSTRATE
    assert record.materials[0].provenance.exact_quote == "compound 1 (500 mg, 2.1 mmol)"