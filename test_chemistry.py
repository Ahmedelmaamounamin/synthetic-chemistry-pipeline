# pip install pytest pytest-mock

import pytest
from unittest.mock import patch
from src.chemistry import ChemicalResolver


def test_process_and_validate_smiles_valid():
    """Test valid SMILES canonicalization and descriptor calculations."""
    # Test with THF SMILES
    raw_smiles = "C1CCOC1"
    data = ChemicalResolver.process_and_validate_smiles(raw_smiles)

    assert data is not None
    assert data["canonical_smiles"] == "C1CCOC1"
    assert data["formula"] == "C4H8O"
    assert data["inchi_key"] == "WYURNTSHIVDZCO-UHFFFAOYSA-N"
    assert pytest.approx(data["mw"], 0.01) == 72.057


def test_process_and_validate_smiles_invalid():
    """Test that invalid SMILES strings return None without crashing."""
    invalid_smiles = "INVALID_SMILES_STRING_123"
    data = ChemicalResolver.process_and_validate_smiles(invalid_smiles)

    assert data is None


@patch("requests.get")
def test_name_to_structure_opsin_success(mock_get):
    """Test OPSIN name-to-structure resolution with mocked HTTP response."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"smiles": "c1ccccc1"}

    smiles = ChemicalResolver.name_to_structure_opsin("benzene")
    assert smiles == "c1ccccc1"


@patch("requests.get")
def test_name_to_structure_pubchem_success(mock_get):
    """Test PubChem API name resolution fallback."""
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "PropertyTable": {
            "Properties": [{"CanonicalSMILES": "CCO"}]
        }
    }

    smiles = ChemicalResolver.name_to_structure_pubchem("ethanol")
    assert smiles == "CCO"


def test_resolve_name_fallback_chain():
    """Test that unresolved compounds return 'Unresolved' status gracefully."""
    with patch.object(ChemicalResolver, "name_to_structure_opsin", return_value=None):
        with patch.object(ChemicalResolver, "name_to_structure_pubchem", return_value=None):
            smiles, source = ChemicalResolver.resolve_name("UnknownChemicalXYZ999")
            assert smiles is None
            assert source == "Unresolved"