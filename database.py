import sqlite3
import json
from pathlib import Path
from src.schemas import ReactionRecord


class ReactionDatabase:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self) -> None:
        """Initializes relational tables and schema structure."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS reactions
                       (
                           reaction_id
                           TEXT
                           PRIMARY
                           KEY,
                           document_id
                           TEXT,
                           procedure_text
                           TEXT,
                           reaction_smiles
                           TEXT,
                           overall_qc_score
                           REAL,
                           requires_review
                           INTEGER,
                           json_data
                           TEXT,
                           created_at
                           TEXT
                       )
                       """)

        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS materials
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           reaction_id
                           TEXT,
                           raw_name
                           TEXT,
                           role
                           TEXT,
                           canonical_smiles
                           TEXT,
                           inchi_key
                           TEXT,
                           mw
                           REAL,
                           FOREIGN
                           KEY
                       (
                           reaction_id
                       ) REFERENCES reactions
                       (
                           reaction_id
                       )
                           )
                       """)

        conn.commit()
        conn.close()

    def save_reaction(self, record: ReactionRecord) -> None:
        """Saves a ReactionRecord into the database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        qc_score = record.quality.overall_score if record.quality else 0.0
        requires_review = 1 if (record.quality and record.quality.requires_human_review) else 0

        cursor.execute("""
            INSERT OR REPLACE INTO reactions 
            (reaction_id, document_id, procedure_text, reaction_smiles, overall_qc_score, requires_review, json_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.reaction_id,
            record.document_id,
            record.procedure_text,
            record.reaction_smiles,
            qc_score,
            requires_review,
            record.model_dump_json(),
            record.extraction_timestamp
        ))

        # Save extracted materials
        for mat in record.materials:
            cursor.execute("""
                           INSERT INTO materials (reaction_id, raw_name, role, canonical_smiles, inchi_key, mw)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """, (
                               record.reaction_id,
                               mat.raw_name,
                               mat.role.value,
                               mat.canonical_smiles,
                               mat.inchi_key,
                               mat.mw
                           ))

        conn.commit()
        conn.close()