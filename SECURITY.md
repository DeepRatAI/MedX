# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in MedeX, please report it responsibly.

### How to Report

**Please do NOT open a public issue for security vulnerabilities.**

Instead, send an email to: **gonzalorome6@gmail.com**

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution Timeline**: Depends on severity
- **Credit**: You will be credited in the fix (unless you prefer anonymity)

### Severity Levels

| Level    | Description                                     | Response Time |
| -------- | ----------------------------------------------- | ------------- |
| Critical | Data breach, RCE, authentication bypass         | 24-48 hours   |
| High     | Significant data exposure, privilege escalation | 1 week        |
| Medium   | Limited impact vulnerabilities                  | 2 weeks       |
| Low      | Minor issues                                    | Next release  |

## Security Best Practices

When using MedeX:

1. **API Keys**: Never commit API keys to version control
2. **Environment Variables**: Use environment variables for secrets
3. **Access Control**: Restrict access to the application appropriately
4. **Data Privacy**: Do not input real patient data in non-compliant environments
5. **Updates**: Keep dependencies updated

## Medical Data Considerations

MedeX handles medical queries and may process sensitive health information:

- Do not use in production healthcare settings without proper compliance review
- Ensure HIPAA/GDPR compliance if handling real patient data
- Implement appropriate access controls and audit logging
- Consider data residency requirements

## Disclosure Policy

- We follow responsible disclosure practices
- Security patches will be released as soon as fixes are verified
- Public disclosure occurs after patch availability

---

Thank you for helping keep MedeX secure! 🔒
