"""
Cryptographically Secure Password Generator
- Uses secrets module (CSPRNG)
- Guarantees character class requirements
- Configurable length and complexity
"""
import secrets
import string

class PasswordGenerator:
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SYMBOLS = "!@#$%^&*()-_=+[]{}|;:',.<>?/"

    @staticmethod
    def generate(
        length: int = 20,
        use_uppercase: bool = True,
        use_digits: bool = True,
        use_symbols: bool = True,
        exclude_ambiguous: bool = False
    ) -> str:
        """Generate a cryptographically secure password."""
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")

        charset = PasswordGenerator.LOWERCASE
        required_chars = [secrets.choice(PasswordGenerator.LOWERCASE)]

        if use_uppercase:
            charset += PasswordGenerator.UPPERCASE
            required_chars.append(secrets.choice(PasswordGenerator.UPPERCASE))
        if use_digits:
            charset += PasswordGenerator.DIGITS
            required_chars.append(secrets.choice(PasswordGenerator.DIGITS))
        if use_symbols:
            charset += PasswordGenerator.SYMBOLS
            required_chars.append(secrets.choice(PasswordGenerator.SYMBOLS))

        if exclude_ambiguous:
            ambiguous = 'il1Lo0O'
            charset = ''.join(c for c in charset if c not in ambiguous)

        # Fill remaining length with random chars from full charset
        remaining = length - len(required_chars)
        password_chars = required_chars + [secrets.choice(charset) for _ in range(remaining)]

        # Securely shuffle (Fisher-Yates via secrets)
        for i in range(len(password_chars) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

        return ''.join(password_chars)

    @staticmethod
    def check_strength(password: str) -> dict:
        """Evaluate password strength and return a score with feedback."""
        score = 0
        feedback = []

        if len(password) >= 12: score += 2
        elif len(password) >= 8: score += 1
        else: feedback.append("Too short — use at least 12 characters")

        if any(c in string.ascii_uppercase for c in password): score += 1
        else: feedback.append("Add uppercase letters")

        if any(c in string.ascii_lowercase for c in password): score += 1
        else: feedback.append("Add lowercase letters")

        if any(c in string.digits for c in password): score += 1
        else: feedback.append("Add numbers")

        if any(c in PasswordGenerator.SYMBOLS for c in password): score += 2
        else: feedback.append("Add special characters")

        if len(set(password)) > len(password) * 0.7: score += 1
        else: feedback.append("Too many repeated characters")

        # Map score to label
        labels = {range(0, 3): "Weak", range(3, 5): "Fair",
                  range(5, 7): "Strong", range(7, 10): "Very Strong"}
        label = next(l for r, l in labels.items() if score in r)

        return {"score": score, "max_score": 8, "label": label, "feedback": feedback}