# SecureVault
[![SecureVault Tests](https://github.com/has990/securevault/actions/workflows/tests.yml/badge.svg)](https://github.com/has990/securevault/actions/workflows/tests.yml)

**SecureVault** is a local-first secure password manager developed as a cybersecurity project. It is designed to demonstrate practical applications of modern cryptography, authentication, integrity protection, secure storage, audit logging, and defensive security controls.

> **Project Status:** Active Development  
> **Category:** Cybersecurity / Secure Software Development / Password Manager  
> **Platform:** Windows and other Python-compatible systems

---

## Overview

SecureVault provides a locally stored vault for managing sensitive credentials and authentication data.

The project focuses on security engineering principles such as:

- Authenticated encryption
- Password-based key derivation
- Additional Authenticated Data (AAD)
- Multi-factor authentication with TOTP
- Vault isolation
- Tamper detection
- Failed-login monitoring and lockout
- Secure audit logging
- Password health analysis
- Data backup and restoration
- Per-password protection
- Duress/decoy vault functionality
- Local-first data storage

SecureVault is intended for **educational, research, and portfolio purposes** and is continuously being improved as new security controls are implemented.

---

## Key Features

### 🔐 Encrypted Vault

Sensitive vault information is encrypted before being stored.

SecureVault uses **AES-GCM authenticated encryption** for protected data. AES-GCM provides both confidentiality and integrity protection for encrypted values.

The project also supports versioned ciphertext so that legacy data can remain compatible while newer data can use authenticated encryption with AAD.

---

### 🧩 Additional Authenticated Data (AAD)

SecureVault uses contextual AAD for newer encrypted records.

Encryption context can include information such as:

- Vault ID
- Entry UUID
- Field type
- TOTP context
- OTP settings context
- Vault credential context

This helps bind encrypted data to its intended security context and makes unauthorized reassignment or tampering detectable during decryption.

---

### 🔑 Password Protection

SecureVault supports two levels of password protection.

**Standard vault protection**

The vault is protected using the application's primary authentication and encryption mechanism.

**Per-password protection**

Individual password entries can additionally be protected using a separate secret phrase.

Protected passwords are stored as encrypted ciphertext rather than plaintext.

---

### 🔢 TOTP / Multi-Factor Authentication

SecureVault supports Time-based One-Time Passwords (TOTP).

Features include:

- TOTP secret storage
- Configurable OTP settings
- TOTP code generation
- OTP entry management
- Enable/disable OTP functionality

TOTP functionality is integrated into the vault authentication workflow.

---

### 🛡️ Tamper Detection

SecureVault maintains an integrity baseline for vault data.

The integrity system can detect unauthorized modifications to protected vault records, including changes involving:

- Vault credentials
- Password entries
- TOTP entries
- OTP settings

Integrity verification is cryptographically protected using **HMAC-SHA256**.

Tamper detection is vault-scoped so that changes belonging to another vault do not incorrectly trigger an integrity failure for the current vault.

---

### 🚨 Failed Login Monitoring and Lockout

SecureVault tracks authentication failures and applies a temporary lockout after repeated unsuccessful attempts.

This provides protection against simple repeated password-guessing attempts.

The application also records security-relevant authentication events for auditing.

---

### 📝 Secure Audit Logging

Security events are recorded in an encrypted local audit log.

The logging system is designed to avoid storing normal audit records as readable plaintext JSON on disk.

Examples of security events include:

- Successful login
- Failed login
- Lockout
- Tamper detection
- Integrity baseline events
- Security-related vault operations

---

### 🔎 Password Health Analysis

SecureVault can analyze stored passwords for security weaknesses such as:

- Weak passwords
- Password reuse
- Password breach exposure

Passwords that use additional per-password protection are treated separately and are not sent to the breach-checking service without first being safely decrypted by the application.

---

### 🌐 Have I Been Pwned Integration

SecureVault supports password breach checking through the **Have I Been Pwned (HIBP)** password API using the k-anonymity approach.

Only the first portion of the SHA-1 hash is sent to the external service rather than the plaintext password.

The application distinguishes between:

- `breached`
- `safe`
- `unknown`

A network or API failure is therefore not incorrectly treated as proof that a password is safe.

---

### 🕵️ Decoy / Duress Vault

SecureVault includes a decoy-vault mechanism designed for situations where the user may need to provide a non-sensitive vault.

The decoy mode maintains separate decoy data from the real vault.

The duress workflow also includes a protected cleanup mechanism for secret data associated with the real vault.

> This feature is a defensive application feature and should not be considered a guarantee of forensic-grade plausible deniability.

---

### 💾 Secure Backup and Restore

SecureVault supports exporting and importing vault data through its backup functionality.

The backup system preserves important security metadata, including:

- Entry UUIDs
- Password-protection state
- Per-password encryption version
- Protected ciphertext
- Vault entry metadata

Versioned encrypted records can therefore be restored without unnecessarily converting protected ciphertext into plaintext during the backup process.

---

### 🔒 Vault Isolation

Database operations are scoped to the active vault.

Operations such as:

- Delete
- Update
- Favorite/unfavorite

verify the associated `vault_id` before modifying a record.

This helps prevent one vault from accidentally modifying another vault's data.

---

### 🗂️ Local Storage

SecureVault follows a **local-first** design.

The main vault database is stored locally rather than requiring a cloud backend.

Database and log files also receive filesystem-permission hardening where supported.

On Windows, the project additionally uses Windows ACL configuration for database-file protection.

---

## Security Architecture

A simplified view of SecureVault's security architecture:

```text
                    ┌─────────────────────┐
                    │      User Login     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Authentication /    │
                    │ Key Derivation      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Vault Key       │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      ┌───────────────┐ ┌──────────────┐ ┌───────────────┐
      │ AES-GCM       │ │ HMAC-SHA256  │ │ TOTP / OTP    │
      │ Encryption    │ │ Integrity    │ │ Authentication │
      └───────┬───────┘ └──────┬───────┘ └───────────────┘
              │                │
              ▼                ▼
      ┌─────────────────────────────────────────────┐
      │               SQLite Database               │
      │                                             │
      │ Entries / TOTP / OTP Settings / Credentials │
      └─────────────────────────────────────────────┘
```

---

## Encryption Design

SecureVault uses authenticated encryption through AES-GCM.

### Encryption Flow

```text
User Secret
    │
    ▼
Key Derivation
    │
    ▼
Vault Encryption Key
    │
    ├──────────────► AES-GCM Encryption
    │                         │
    │                         ▼
    │                  Ciphertext + Nonce
    │
    └──────────────► HMAC Integrity Verification
```

For newer encrypted records, SecureVault also uses contextual AAD.

Example:

```text
Vault ID
   +
Entry UUID
   +
Field Name
   │
   ▼
Canonical AAD Context
   │
   ▼
AES-GCM Encryption / Decryption
```

This allows encrypted data to be associated with its intended record and field context.

---

## Encryption Versioning

SecureVault supports versioned encrypted data.

### V1

Legacy encrypted records use the original ciphertext format without AAD.

### V2

Newer encrypted records use a version marker and AAD-aware AES-GCM encryption.

The application maintains compatibility with existing V1 records while allowing newer records to benefit from contextual binding.

---

## Database Structure

SecureVault uses SQLite for local storage.

The database contains security-related information such as:

```text
vault_credentials
entries
totp_entries
otp_settings
```

Password entries contain identifiers and encrypted values rather than requiring plaintext password storage.

Each entry also receives a stable UUID used by security-sensitive encryption contexts and backup/restore operations.

---

## Project Structure

```text
securevault/
│
├── core/
│   ├── database.py
│   ├── encryption.py
│   ├── crypto_context.py
│   ├── breach_checker.py
│   ├── password_health.py
│   ├── per_password_lock.py
│   ├── tamper_detection.py
│   ├── secure_log_store.py
│   ├── duress_handler.py
│   └── ...
│
├── gui/
│   ├── app.py
│   ├── login_view.py
│   ├── vault_view.py
│   ├── settings_view.py
│   ├── security_dashboard.py
│   ├── add_entry_dialog.py
│   └── ...
│
├── tests/
│   ├── test_encryption.py
│   ├── test_totp_manager.py
│   ├── test_tamper_detection.py
│   ├── test_intruder_log.py
│   ├── test_duress_handler.py
│   ├── test_vault_isolation.py
│   ├── test_breach_checker.py
│   ├── test_password_health.py
│   ├── test_per_password_lock.py
│   ├── test_secure_export.py
│   └── ...
│
├── main.py
├── requirements.txt
├── README.md
├── SECURITY.md
└── project_report.md
```

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| SQLite | Local vault database |
| AES-GCM | Authenticated encryption |
| HMAC-SHA256 | Integrity verification |
| TOTP | Multi-factor authentication |
| SHA-1 / HIBP k-anonymity | Password breach checking |
| Pytest | Automated testing |
| Tkinter | Desktop graphical interface |
| Windows ACLs | Filesystem access control |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/USERNAME/securevault.git
cd securevault
```

Replace `USERNAME` with your GitHub username.

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Running SecureVault

Start the application with:

```bash
python main.py
```

The application will initialize the required local storage and launch the graphical interface.

---

## Running the Tests

SecureVault includes automated security and regression tests.

Run the complete test suite:

```bash
pytest -q
```

Run the encryption tests:

```bash
pytest tests/test_encryption.py -q
```

Run the TOTP tests:

```bash
pytest tests/test_totp_manager.py -q
```

Run the tamper-detection tests:

```bash
pytest tests/test_tamper_detection.py -q
```

Run the vault-isolation tests:

```bash
pytest tests/test_vault_isolation.py -q
```

---

## Security Testing Coverage

The test suite covers important security properties including:

```text
✓ AES-GCM encryption/decryption
✓ Wrong-key rejection
✓ Authentication-tag validation
✓ AAD validation
✓ Legacy encryption compatibility
✓ TOTP database handling
✓ TOTP regression protection
✓ Tamper detection
✓ Wrong-key integrity verification
✓ Missing integrity baseline handling
✓ Vault-scoped integrity checks
✓ Authentication lockout
✓ Intruder logging
✓ Duress-vault cleanup
✓ Vault isolation
✓ Entry UUID uniqueness
✓ Password breach states
✓ Password-health analysis
✓ Per-password encryption
✓ Wrong per-password context rejection
✓ Secure backup/restore
✓ Protected-password backup compatibility
✓ Database initialization
✓ File-security controls
✓ Encrypted audit logging
```

Run the complete test suite to see the current test count and results:

```bash
pytest -q
```

---

## Threat Model

SecureVault considers several common threats against a locally stored password manager.

### Credential Theft

An attacker obtaining the vault database should not automatically obtain plaintext passwords.

### Database Modification

An attacker modifying protected records should be detectable through integrity verification and authenticated encryption.

### Password Guessing

Repeated failed login attempts are monitored and can trigger temporary lockout.

### Cross-Vault Access

Database operations are scoped to the relevant vault to reduce unauthorized cross-vault modifications.

### Password Reuse

The password-health system can identify reused passwords among entries that can safely be analyzed.

### Breached Credentials

Passwords can be checked against breach information using the HIBP k-anonymity model.

### Unauthorized Configuration Changes

TOTP and OTP settings are included in protected vault integrity data.

---

## Security Considerations

SecureVault is designed with defensive security principles in mind, but it is important to understand the scope of the project.

This project should **not** be described as:

- Unhackable
- Perfectly secure
- Forensically undetectable
- Guaranteed zero-knowledge
- Guaranteed secure memory erasure
- Forensic-grade plausible deniability

Like all security software, SecureVault can contain vulnerabilities and implementation limitations.

The project is intended to demonstrate secure software engineering practices and provide a foundation for continued security research and improvement.

---

## Security Best Practices

When using SecureVault:

- Use a strong and unique master password.
- Enable TOTP where appropriate.
- Keep backups protected and stored securely.
- Do not share master passwords or secret phrases.
- Keep the application dependencies updated.
- Review security warnings and integrity alerts.
- Do not use experimental builds as the sole protection for highly sensitive credentials.

---

## Responsible Security Disclosure

Security issues should be reported privately rather than publicly disclosed before they can be investigated.

Please see [`SECURITY.md`](SECURITY.md) for the project's security-reporting policy.

---

## Development Goals

Future development may focus on areas such as:

- Stronger key management
- Improved secure-memory handling
- More extensive authentication controls
- Expanded automated security testing
- Improved backup encryption
- Better recovery mechanisms
- Additional database-hardening techniques
- Improved Windows security integration
- Security-focused CI/CD
- Code quality and architecture improvements
- Expanded threat-model documentation

---

## Educational Purpose

SecureVault was developed as a cybersecurity learning and portfolio project.

The project demonstrates practical concepts from:

- Applied Cryptography
- Information Security
- Secure Software Development
- Authentication
- Database Security
- Security Monitoring
- Integrity Verification
- Threat Modeling
- Defensive Programming
- Software Testing

It is intended to show how theoretical cybersecurity concepts can be implemented in a real software project.

---

## Author

**Hasnain Awan**

Cybersecurity Student  
Pakistan

---

## License

This project is currently provided for educational and portfolio purposes.

A formal open-source license can be added to the repository when the project is ready for public distribution.

---

## Disclaimer

SecureVault is a student-developed security project.

Although security mechanisms have been implemented and tested, no software can be guaranteed to be completely secure.

Do not use the project as the sole protection mechanism for highly sensitive or mission-critical credentials without independently reviewing the implementation and its security assumptions.
