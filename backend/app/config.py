"""
App-level configuration (auth + database).

Loads a `.env` file (if present) so `MONGODB_URI` / `JWT_SECRET_KEY`
etc. don't have to be exported manually on every shell. Falls back to
sane local-dev defaults where it's safe to do so; fails loudly for
anything security-sensitive that's missing in production.
"""

import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/border")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "border")

# HS256 signing key for JWTs. Generate your own for real deployments,
# e.g.: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # 24h default
