# Security Policy

## Project Status

SecureVault is an actively developed cybersecurity project intended for educational, research, and portfolio purposes.

Security issues may exist because the project is still under development. Users should review the implementation and security assumptions before relying on SecureVault for highly sensitive credentials.

---

## Supported Versions

| Version | Supported |
|---|---|
| Development / Latest | ✅ Yes |
| Older versions | ❌ No |

Only the latest development version is actively considered for security fixes.

---

## Reporting a Vulnerability

If you discover a security vulnerability in SecureVault, please report it privately before making the issue public.

When reporting a vulnerability, provide as much of the following information as possible:

- A clear description of the vulnerability
- The affected component or file
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Potential security impact
- Proof of concept, when appropriate
- Suggested mitigation, if available

Please do **not** include real passwords, private keys, authentication secrets, or other sensitive information in a vulnerability report.

---

## Security Issues That Should Be Reported

Examples include:

- Authentication bypass
- Unauthorized vault access
- Cross-vault data access
- Cryptographic implementation flaws
- Encryption or decryption vulnerabilities
- Authentication-tag bypass
- AAD validation weaknesses
- Integrity or tamper-detection bypass
- TOTP authentication weaknesses
- Password-protection bypass
- Sensitive data exposure
- Plaintext credential leakage
- Backup or restore vulnerabilities
- Privilege or access-control issues
- Security-sensitive database manipulation
- Vulnerabilities that could allow unauthorized code or data access

---

## Out of Scope

The following are generally outside the scope of the project's security reporting process:

- Issues requiring physical access to an already unlocked system
- Social engineering attacks
- Denial-of-service attacks with no confidentiality or integrity impact
- Vulnerabilities in third-party services that are not caused by SecureVault
- Issues that depend entirely on malicious modification of the user's operating system
- Cosmetic or non-security-related application bugs
- Self-inflicted data loss caused by misuse of experimental features

---

## Responsible Disclosure

Security researchers are requested to allow reasonable time for investigation and remediation before publicly disclosing a vulnerability.

Please avoid:

- Publicly posting an exploitable vulnerability before it has been investigated
- Accessing or modifying data belonging to other users
- Destroying data
- Performing unnecessary denial-of-service testing
- Using discovered vulnerabilities for malicious purposes

Security testing should be performed only against systems and data you are authorized to test.

---

## Security Improvements

SecureVault is continuously being improved with security-focused development and testing.

Current security areas include:

- AES-GCM authenticated encryption
- Additional Authenticated Data (AAD)
- HMAC-SHA256 integrity verification
- Vault-scoped integrity checks
- TOTP authentication
- Failed-login monitoring and lockout
- Encrypted audit logging
- Password health analysis
- Password breach checking
- Per-password protection
- Vault isolation
- Secure backup and restoration
- Filesystem security controls
- Automated security and regression testing

---

## Disclaimer

SecureVault is a student-developed security project.

No software can be guaranteed to be completely secure. SecureVault should not be considered unhackable, forensically undetectable, or guaranteed to provide perfect protection against every threat.

Use the software responsibly and understand its security limitations before storing sensitive information.