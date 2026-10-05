"""Runtime configuration, populated from `.env` and the process environment."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All tunables in one place.

    Every value can be overridden by an environment variable of the same name,
    which is how `.env` feeds it. Nothing here reads the environment directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Providers ----------------------------------------------------------
    google_api_key: str | None = Field(default=None, repr=False)
    google_cloud_project: str | None = None
    google_application_credentials: Path | None = None
    tavily_api_key: str | None = Field(default=None, repr=False)

    # Model ids are pinned explicitly rather than tracked: Gemini preview names
    # churn, and an unpinned "latest" silently changes behaviour between runs.
    gemini_agent_model: str = "gemini-3.1-pro-preview"
    gemini_fast_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-001"

    # --- Voiceover (Chirp 3 HD) --------------------------------------------
    tts_voice: str = "en-US-Chirp3-HD-Kore"
    tts_language: str = "en-US"
    tts_speaking_rate: float = Field(default=1.0, ge=0.25, le=2.0)

    # --- Vector store (memory MCP) -----------------------------------------
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = Field(default=None, repr=False)

    # --- Render node --------------------------------------------------------
    render_node_url: str = "http://localhost:8000"
    render_node_token: str | None = Field(default=None, repr=False)
    render_image: str = "vwiz/render-node:latest"
    render_timeout_s: int = 300
    render_memory: str = "2g"
    render_cpus: str = "2"
    render_pids_limit: int = 256
    render_max_output_bytes: int = 200 * 1024 * 1024

    # --- Preview vs final quality ------------------------------------------
    # The right-hand panel shows a fast low-quality draft; final renders use the
    # full quality setting. Manim quality flags, cheapest first.
    preview_quality: str = "-ql"
    final_quality: str = "-qh"
    preview_fps: int = 15

    # --- Cost guards --------------------------------------------------------
    # Primary defence against runaway spend: every metered step scales with these.
    max_scenes: int = 12
    max_total_duration_s: float = 180.0
    max_render_attempts: int = 3
    max_pdf_pages: int = 300
    max_upload_bytes: int = 32 * 1024 * 1024
    max_document_chars: int = 2_000_000
    # `.docx`/`.odt` are zip archives, so the upload cap bounds compressed bytes
    # only. This caps the *expanded* size, read from the zip central directory
    # before anything is inflated.
    max_archive_expanded_bytes: int = 256 * 1024 * 1024

    # --- Paths --------------------------------------------------------------
    data_dir: Path = Path("./data")

    @property
    def projects_dir(self) -> Path:
        return self.data_dir / "projects"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def renders_dir(self) -> Path:
        return self.data_dir / "renders"

    def ensure_dirs(self) -> None:
        """Create the data tree. Safe to call repeatedly."""
        for directory in (self.projects_dir, self.uploads_dir, self.renders_dir):
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def accepted_upload_types(self) -> list[str]:
        """Extensions offered to the file uploader, derived from the extractors."""
        from vwiz.ingest import SUPPORTED_SUFFIXES

        return [suffix.lstrip(".") for suffix in SUPPORTED_SUFFIXES]

    def missing_credentials(self) -> list[str]:
        """Which credentials are absent, for display in the UI."""
        missing = []
        if not self.google_api_key:
            missing.append("GOOGLE_API_KEY")
        if not self.google_cloud_project:
            missing.append("GOOGLE_CLOUD_PROJECT")
        return missing


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the environment is parsed once per process."""
    return Settings()
