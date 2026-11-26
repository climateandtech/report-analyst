#!/usr/bin/env python3
"""Mint a one-time JWT for POST /admin/question-sets (enterprise instances)."""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

from joserfc import jwt
from joserfc.jwk import OctKey


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint questionset upload JWT")
    parser.add_argument("--iss", default=os.getenv("QUESTIONSETS_JWT_ISS", "climateandtech-ops"))
    parser.add_argument("--sub", default="upload@ops")
    parser.add_argument("--ttl", type=int, default=300, help="Token lifetime in seconds")
    parser.add_argument(
        "--secret",
        default=os.getenv("QUESTIONSETS_JWT_HMAC_SECRET"),
        help="HMAC secret (dev; production use Ed25519 private key tooling)",
    )
    args = parser.parse_args()
    if not args.secret:
        print("Set QUESTIONSETS_JWT_HMAC_SECRET or pass --secret", file=sys.stderr)
        raise SystemExit(1)

    now = datetime.now(timezone.utc)
    claims = {
        "iss": args.iss,
        "sub": args.sub,
        "aud": os.getenv("QUESTIONSETS_JWT_AUDIENCE", "report-analyst-questionset-admin"),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=args.ttl)).timestamp()),
        "jti": str(uuid.uuid4()),
        "scope": "questionset:write",
    }
    key = OctKey.import_key(args.secret)
    token = jwt.encode({"alg": "HS256"}, claims, key)
    print(token)


if __name__ == "__main__":
    main()
