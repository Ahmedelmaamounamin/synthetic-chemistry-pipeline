import os
from pathlib import Path
from pydantic import BaseModel


class PipelineConfig(BaseModel):
    # Windows network/local path configuration
    base_dir: Path = Path(r"path")
    materials_dir: Path = Path(r"path\materials")
    output_dir: Path = Path(r"path\output")
    cache_dir: Path = Path(r"path\cache")
    db_path: Path = Path(r"path\output\reactions.db")

    # OpenRouter API Credentials & Base URL
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Free Model Options on OpenRouter:
    # - "openrouter/auto"                        (Lets OpenRouter route automatically)
    # - "meta-llama/llama-3.3-70b-instruct:free" (Recommended for structured JSON output)
    # - "google/gemini-2.0-flash-lite-001:free" (Fast, high context window)
    # - "deepseek/deepseek-r1:free"             (Reasoning-focused)
    extraction_model: str = "meta-llama/llama-3.3-70b-instruct:free"

    # OpenRouter App Identification Headers
    site_url: str = "http://localhost:8000"
    site_name: str = "Synthetic Chemistry Extraction Pipeline"

    # Validation Thresholds
    min_quality_score_threshold: float = 7.0

    def setup_directories(self) -> None:
        """Ensure all required pipeline directories exist on the filesystem."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)


config = PipelineConfig()