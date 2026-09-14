"""
Global Configuration Settings for KubeLabs Backend.
Sets up sys.path for monorepo packages.
"""

import sys
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Monorepo root is 4 levels up from this file (apps/api/src/core/config.py -> parents[4] is workspace root)
MONOREPO_ROOT = Path(__file__).resolve().parents[4]

# Ensure monorepo packages are on sys.path
for pkg in ["lab_schema", "validator_core", "sandbox_runtime", "incident_core"]:
    pkg_src = str(MONOREPO_ROOT / "packages" / pkg / "src")
    if pkg_src not in sys.path:
        sys.path.insert(0, pkg_src)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True)

    PROJECT_NAME: str = "KubeLabs SRE Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Environment
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./kubelabs.db"

    # Cache & Distributed Locking
    REDIS_URL: Optional[str] = None

    # Security & Sandbox
    SANDBOX_TTL_SECONDS: int = 1800
    ENABLE_PODMAN: bool = True
    PODMAN_BINARY: str = "podman"

    # Paths
    BASE_DIR: Path = MONOREPO_ROOT
    LABS_DIR: Path = MONOREPO_ROOT / "labs"
    CONTENT_DIR: Path = MONOREPO_ROOT / "content"


settings = Settings()
