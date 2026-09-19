# Local authentication reference

Synthetic local-auth API for isolated development and CI. Never use shared or
production secrets with its isolated fixtures. Supply DATABASE_URL,
LKS_AUTH_ENVIRONMENT, LKS_AUTH_ORIGIN (exact HTTPS), LKS_AUTH_ISSUER,
LKS_AUTH_AUDIENCE and LKS_AUTH_KEYRING_FILE externally. The JSON keyring contains
`current` and `keys`, with random keys encoded as base64 (at least 32 bytes).
There are no default signing keys or public signup/recovery-by-email endpoints.

Run migrations before the service; provisioning is an explicit operator step.
`python -m local_auth.provision` reads a protected external synthetic fixture
file only in the two isolated environments. It never fetches consumer datasets.
Refresh tokens and assisted-recovery tokens are stored as hashes; passwords use
Argon2id with a versioned policy and individual salts. HTTP logs must not include
headers/bodies. Production, MFA, federation and native mobile clients are outside
this profile's supported scope.

Contract: GET /records; GET /records/{identifier}; POST /records. Login,
refresh, password changes and audit writes are not evidence of this contract's
business persistence. PostgreSQL must independently observe the created record.

Security rationale: [OWASP password storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
and [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html).
