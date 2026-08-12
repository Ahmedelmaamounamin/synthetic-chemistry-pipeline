import uuid
from pathlib import Path
from src.config import config
from src.ingestion import PDFIngestor
from src.chunking import ProcedureDetector
from src.extraction import ChemistryExtractor
from src.normalization import QuantityNormalizer
from src.chemistry import ChemicalResolver
from src.validation import QualityControlEngine
from src.database import ReactionDatabase


def run_pipeline():
    print("[1/6] Initializing Pipeline Configuration...")
    config.setup_directories()

    ingestor = PDFIngestor(config.materials_dir)
    detector = ProcedureDetector()
    extractor = ChemistryExtractor()
    qc_engine = QualityControlEngine()
    db = ReactionDatabase(config.db_path)

    pdf_files = ingestor.discover_pdf_files()
    print(f"[2/6] Discovered {len(pdf_files)} PDF documents in materials path.")

    for pdf_path in pdf_files:
        print(f"\nProcessing File: {pdf_path.name}")
        chunks = ingestor.extract_text_with_provenance(pdf_path)
        experimental_chunks = detector.extract_procedures(chunks)

        print(f" -> Found {len(experimental_chunks)} experimental procedure sections.")

        for chunk in experimental_chunks:
            rxn_id = f"RXN-{uuid.uuid4().hex[:8].upper()}"

            # Pass 1: Generative LLM Structured Extraction
            print(" -> Running Generative LLM Extraction...")
            record = extractor.extract_reaction(chunk.text, doc_id=chunk.document_id, page_num=chunk.page_number)
            record.reaction_id = rxn_id

            # Pass 2: Chemical Structure Resolution & Quantity Normalization
            print(" -> Normalizing Chemical Entities & Physical Quantities...")
            for mat in record.materials:
                # Name to Structure Resolution via OPSIN / PubChem / RDKit
                smiles, source = ChemicalResolver.resolve_name(mat.raw_name)
                mat.smiles = smiles
                mat.structure_source = source

                if smiles:
                    rdkit_data = ChemicalResolver.process_and_validate_smiles(smiles)
                    if rdkit_data:
                        mat.canonical_smiles = rdkit_data["canonical_smiles"]
                        mat.inchi_key = rdkit_data["inchi_key"]
                        mat.formula = rdkit_data["formula"]
                        mat.mw = rdkit_data["mw"]

                # Unit Normalization via Pint
                if mat.mass and mat.mass.raw_text:
                    mat.mass.normalized = QuantityNormalizer.normalize_quantity(mat.mass.raw_text)
                if mat.moles and mat.moles.raw_text:
                    mat.moles.normalized = QuantityNormalizer.normalize_quantity(mat.moles.raw_text)

            # Pass 3: Deterministic Quality Control Evaluation
            print(" -> Running Deterministic Quality Control & Verification...")
            record.quality = qc_engine.evaluate_record(record)

            # Pass 4: Persistence to Relational Database
            db.save_reaction(record)
            print(
                f" -> Successfully processed & saved reaction {rxn_id} (QC Score: {record.quality.overall_score}/10.0)")


if __name__ == "__main__":
    run_pipeline()