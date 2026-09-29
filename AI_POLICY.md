# CIB Mango Tree — AI Use Policy

**Effective:** August 2026
**Applies to:** CIB Mango Tree contributors

### In short

1. You remain responsible — review AI output before you commit, ship, or rely on it.
2. Do not put secrets or private data into AI unless the service is approved for that information.
3. When unsure, stop and ask before proceeding.

## 1. Purpose

CIB Mango Tree supports the responsible use of artificial intelligence (AI) as a tool for building software, solving problems, doing research, and improving day-to-day work.

AI can make us more productive, but it also introduces risks around security, privacy, intellectual property, accuracy, and unintended behavior. This policy establishes a few practical rules for using AI without unnecessarily limiting experimentation and innovation.

## 2. Use AI Where It Helps

AI may be used for legitimate CIB Mango Tree work, including:

- Writing, refactoring, debugging, and testing code
- Research and technical investigation
- Prototyping and proof-of-concept work
- Documentation and technical writing
- Brainstorming and design exploration
- Data transformation and analysis
- Automating repetitive development tasks
- Reviewing or explaining existing code and technical material

AI is a tool, not an authority. Use it to accelerate your work, not to replace engineering judgment.

## 3. Protect Our Data

**Do not put confidential or sensitive information into an AI service unless that service has been explicitly approved for that information.**

Concrete examples of what **not** to paste into an AI chat or agent:

- Contents of `.env` files, signing certificates, or store/partner portal secrets
- Real customer datasets, exports with personal identifiers, or production database dumps

Never provide an AI service with:

- Passwords, API keys, tokens, certificates, or other credentials
- User personal information
- Confidential information
- Private financial, personnel, or contractual information
- Security-sensitive information that does not need to be disclosed
- Information that CIB Mango Tree is contractually or legally required to protect

When working with AI, use the minimum information necessary. Prefer sanitized, synthetic, or representative data whenever possible — for example, fake names and IDs in a small sample file instead of a live export.

## 4. Review AI-Generated Work

**The person using AI remains responsible for the resulting work.**

AI-generated code, documentation, analysis, or other output must be reviewed before it is committed, deployed, published, or relied upon.

For software, review should include the same things we would review in human-written code:

- Does it address the specific problem addressed in the issue?
- Is it reviewable by a human, within a reasonable timeframe?
- Is it secure?
- Is it maintainable?
- Does it introduce unnecessary dependencies?
- Does it comply with applicable licenses?
- Does it do anything unexpected?

Do not assume that an answer is correct simply because an AI system presents it confidently.

## 5. AI in the Development Environment

AI coding assistants and agents may be used where appropriate, subject to the same security and data-handling requirements as any other development tool.

AI agents must be given **only the access they need** to perform their intended task.

Before allowing an AI agent to modify code, execute commands, access credentials, interact with external services, or make changes to shared infrastructure, consider the potential consequences of an incorrect or malicious action.

AI-generated changes remain subject to normal source-control, review, testing, and deployment processes.

## 6. Intellectual Property and Third-Party Material

AI does not change our obligations regarding copyright, software licenses, confidentiality, or intellectual property.

Do not intentionally use AI to reproduce proprietary or confidential material belonging to another party.

AI-generated code should be reviewed for licensing and attribution concerns before being incorporated into a product or distributed outside the organization.

## 7. Prohibited Uses

AI must not be used to:

- Circumvent authentication, authorization, security controls, or monitoring
- Expose or obtain information that the user is not authorized to access
- Generate or distribute fraudulent, deceptive, discriminatory, harassing, or unlawful material
- Make consequential decisions about people without appropriate human oversight
- Bypass CIB Mango Tree's normal engineering, security, or approval processes
- Grant an AI system unnecessary or uncontrolled access to organization systems or data

## 8. When in Doubt

If you are unsure whether an AI tool, dataset, integration, or use case is appropriate, **stop and ask before proceeding** — contact the CIB team.

**Reporting.** Promptly report AI-related security incidents, accidental disclosure of information, unexpected agent behavior, or other policy concerns to the team. Do not wait to "fix it first" if sensitive information may already have been exposed.

This policy will be reviewed periodically as AI capabilities, tooling, and the organization's needs evolve.

**The objective is simple: use AI where it makes us better, but remain responsible for what it does.**
