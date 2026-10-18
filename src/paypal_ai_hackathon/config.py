"""Typed settings loaded from environment variables and `.env`."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Claude
    anthropic_api_key: SecretStr | None = None  # unset is fine if `ant auth login` was used
    claude_model: str = "claude-opus-5-5"
    claude_effort: Literal["low", "medium", "high", "xhigh", "max"] = "medium"

    # PayPal (sandbox only during the hackathon)
    paypal_client_id: str = ""
    paypal_client_secret: SecretStr = SecretStr("")
    paypal_environment: Literal["SANDBOX", "PRODUCTION"] = "SANDBOX"

    # Phoenix / OpenTelemetry
    phoenix_collector_endpoint: str = "http://localhost:6006/v1/traces"
    phoenix_project_name: str = "paypal-ai-hackathon"
    tracing_enabled: bool = True

    @property
    def paypal_sandbox(self) -> bool:
        return self.paypal_environment == "SANDBOX"

    @property
    def paypal_base_url(self) -> str:
        if self.paypal_sandbox:
            return "https://api-m.sandbox.paypal.com"
        return "https://api-m.paypal.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
