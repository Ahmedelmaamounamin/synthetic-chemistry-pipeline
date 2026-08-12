import datetime
from typing import Optional
import instructor
from openai import OpenAI
from src.schemas import ReactionRecord
from src.config import config


class ChemistryExtractor:
    def __init__(self, api_key: Optional[str] = None):
        key = api_key or config.openrouter_api_key
        if not key:
            raise ValueError(
                "OpenRouter API Key not found. Please set OPENROUTER_API_KEY "
                "in your environment variables or config.py."
            )

        # 1. Initialize OpenAI client pointing to OpenRouter's endpoint
        self.raw_openai_client = OpenAI(
            base_url=config.openrouter_base_url,
            api_key=key,
            default_headers={
                "HTTP-Referer": config.site_url,
                "X-Title": config.site_name,
            }
        )

        # 2. Wrap client with Instructor using JSON mode for broad model compatibility
        self.client = instructor.from_openai(
            self.raw_openai_client,
            mode=instructor.Mode.JSON
        )
        self.model = config.extraction_model

    def extract_reaction(self, procedure_text: str, doc_id: str, page_num: int) -> ReactionRecord:
        """Runs multi-pass structured extraction using OpenRouter."""

        system_prompt = (
            "You are an expert synthetic chemistry data extraction engine. "
            "Your task is to extract chemical entities, parameters, workup procedures, and yields "
            "from experimental procedure text into the specified structured JSON schema.\n\n"
            "CRITICAL RULES:\n"
            "1. NEVER invent or extrapolate values not directly stated in the text.\n"
            "2. Ensure exact text quotes are attached to all provenances.\n"
            "3. Correctly classify roles: Substrate, Reagent, Solvent, Catalyst, Product, Base, etc.\n"
            "4. Leave unknown fields as null."
        )

        user_prompt = f"Extract the synthetic reaction record from this experimental text:\n\n{procedure_text}"

        try:
            # Instructor enforces the Pydantic schema over OpenRouter's response
            extracted: ReactionRecord = self.client.chat.completions.create(
                model=self.model,
                response_model=ReactionRecord,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0
            )
        except Exception as e:
            print(f"[ERROR] OpenRouter extraction failed for document {doc_id}: {str(e)}")
            raise e

        # Inject metadata
        extracted.document_id = doc_id
        extracted.procedure_text = procedure_text
        extracted.extraction_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        extracted.model_version = f"openrouter/{self.model}"

        return extracted