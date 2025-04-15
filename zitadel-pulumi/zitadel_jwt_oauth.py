#!/usr/bin/env python3

import jwt
import datetime
import json
import os
import requests
import sys

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# --- CONFIG ---
CUSTOM_DOMAIN = os.getenv("CUSTOM_DOMAIN")
if not CUSTOM_DOMAIN:
    eprint("Error: CUSTOM_DOMAIN environment variable is not set.")
    sys.exit(1)

ZITADEL_AUDIENCE = f"https://{CUSTOM_DOMAIN}"
OAUTH_TOKEN_URL = f"https://{CUSTOM_DOMAIN}/oauth/v2/token"
SCOPES = "openid urn:zitadel:iam:org:project:id:zitadel:aud"

# --- LOAD SERVICE ACCOUNT FILE ---
try:
    with open("zitadel-admin-sa.json", "r") as f:
        sa = json.load(f)
except Exception as e:
    eprint(f"Error reading zitadel-admin-sa.json: {e}")
    sys.exit(1)

try:
    service_user_id = sa["userId"]
    private_key = sa["key"]
    key_id = sa["keyId"]
except KeyError as e:
    eprint(f"Missing expected field in service account JSON: {e}")
    sys.exit(1)

# --- GENERATE JWT ---
now = datetime.datetime.now(datetime.timezone.utc)
payload = {
    "iss": service_user_id,
    "sub": service_user_id,
    "aud": ZITADEL_AUDIENCE,
    "exp": now + datetime.timedelta(minutes=5),
    "iat": now,
}

header = {
    "alg": "RS256",
    "kid": key_id
}

try:
    signed_jwt = jwt.encode(payload, private_key, algorithm="RS256", headers=header)
except Exception as e:
    eprint(f"Failed to encode JWT: {e}")
    sys.exit(1)

# --- REQUEST ACCESS TOKEN ---
form = {
    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
    "scope": SCOPES,
    "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
    "assertion": signed_jwt
}

try:
    response = requests.post(OAUTH_TOKEN_URL, data=form, headers={
        "Content-Type": "application/x-www-form-urlencoded"
    })
except Exception as e:
    eprint(f"HTTP request to ZITADEL failed: {e}")
    sys.exit(1)

if response.status_code != 200:
    eprint(f"ZITADEL token request failed with status {response.status_code}")
    try:
        eprint(response.json())
    except Exception:
        eprint(response.text)
    sys.exit(1)

try:
    access_token = response.json()["access_token"]
    print(access_token)
except KeyError:
    eprint("Access token not found in response.")
    sys.exit(1)