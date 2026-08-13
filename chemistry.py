import urllib.parse
from typing import Any, Dict, Optional, Tuple
import requests
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors


class ChemicalResolver:
    """Resolves chemical names to structure representations using OPSIN, PubChem, and RDKit."""

    @staticmethod
    def name_to_structure_opsin(name: str) -> Optional[str]:
        """Resolves systematic IUPAC chemical names to SMILES using the OPSIN REST API."""
        try:
            encoded_name = urllib.parse.quote(name)
            url = f"https://opsin.ch.cam.ac.uk/opsin/{encoded_name}.json"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get("smiles")
        except Exception:
            pass
        return None

    @staticmethod
    def name_to_structure_pubchem(name: str) -> Optional[str]:
        """Fallback lookup to resolve chemical names/synonyms via the PubChem PUG-REST API."""
        try:
            encoded_name = urllib.parse.quote(name)
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded_name}/property/CanonicalSMILES/JSON"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                props = data["PropertyTable"]["Properties"][0]
                return props.get("ConnectivitySMILES") or props.get("CanonicalSMILES")
        except Exception:
            pass
        return None

    @classmethod
    def resolve_name(cls, name: str) -> Tuple[Optional[str], Optional[str]]:
        """Resolves a name string, returning (SMILES, Resolution_Source)."""
        # Step 1: OPSIN (IUPAC Parser)
        smiles = cls.name_to_structure_opsin(name)
        if smiles:
            return smiles, "OPSIN"

        # Step 2: PubChem Lookup
        smiles = cls.name_to_structure_pubchem(name)
        if smiles:
            return smiles, "PubChem"

        return None, "Unresolved"

    @staticmethod
    def process_and_validate_smiles(smiles: str) -> Optional[Dict[str, Any]]:
        """Validates SMILES strings using RDKit and computes canonical structural descriptors."""
        if not smiles:
            return None

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None  # Invalid structure

        # Compute canonical descriptors
        canonical_smiles = Chem.MolToSmiles(mol, canonical=True)
        inchi_key = Chem.MolToInchiKey(mol)
        formula = rdMolDescriptors.CalcMolFormula(mol)
        mw = Descriptors.ExactMolWt(mol)

        return {
            "canonical_smiles": canonical_smiles,
            "inchi_key": inchi_key,
            "formula": formula,
            "mw": mw
        }
