# Passkey verification

13 October 2026: Playwright Chromium with a CDP CTAP2 resident-key virtual authenticator successfully registered a passkey through the HomeAtlas security UI, signed out, signed in using the passkey UI, and read the correct authenticated household. No browser errors were captured. Registration used the real Better Auth endpoint and PostgreSQL, with the actual local verification-email link.

This exercises browser WebAuthn protocol and session handling. It does not certify physical Touch ID, Face ID, hardware security keys, cross-device credential syncing, or production HTTPS origin configuration.
