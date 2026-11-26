# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 2.0.x | Yes |
| < 2.0 | No |

## Security Model

MELTDOWN is an offline terminal game:
- It makes **no network requests** and collects **no telemetry or personal data**.
- Save data is stored locally as plain JSON in `~/.meltdown/data.json` (or `MELTDOWN_DATA_DIR`).
- It does not execute shell commands or deserialize untrusted binary formats (no `pickle` or `eval`).

## Reporting a Vulnerability

If you discover a security or safety issue (such as unsafe file handling or terminal escape injection):

1. **Do not** open a public GitHub issue with exploit details.
2. Contact the maintainer via GitHub Security Advisories at:
   https://github.com/codest0411/meltdown/security/advisories
3. Include steps to reproduce, affected OS/Python version, and potential impact.

We will acknowledge reports and work on a fix promptly.
