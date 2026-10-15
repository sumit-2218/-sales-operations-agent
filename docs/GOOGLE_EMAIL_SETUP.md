# Google sign-in and email delivery setup

## Google sign-in
1. In Google Cloud Console, create/select a project and configure the OAuth consent screen.
2. Create an OAuth client ID of type **Web application**.
3. Add `http://localhost:5173` (and your production frontend origin) to Authorized JavaScript origins.
4. Put the same client ID in project-root `.env` as `GOOGLE_CLIENT_ID` and `frontend/.env` as `VITE_GOOGLE_CLIENT_ID`.
5. Install updated backend requirements and restart both services. The backend verifies the Google ID token, checks the audience and `email_verified`, and then issues the app's own JWT. Do not trust a client-supplied email without this verification.

Google sign-in only proves that the Google account email is verified. It does not send a separate verification email for password-based registration; use a transactional verification flow if that is required too.

## Send an outreach email
Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL` in the root `.env`. For Gmail, use an app password only when eligible and with 2-Step Verification enabled. Do not use your normal Google password. Restart the backend. In Outreach, save the draft, check the recipient and message, then click **Send email** and confirm. Sending is user-initiated and requires a lead email address.

## Important: automatically replying when a lead replies
This package intentionally does **not** automatically send a follow-up in response to inbound email. SMTP sends mail out; it does not monitor replies. Safe automation requires a connected inbox (for example Gmail API OAuth with narrowly scoped permissions), inbound notifications or polling, message/thread matching, duplicate-event protection, an opt-in reply policy, suppression/opt-out handling, and limits to prevent loops or repeated unsolicited email. Configure that separately and test with an internal mailbox before enabling it. Do not expose an unauthenticated inbound webhook or automatically send AI-generated replies without human review.

## Production checklist
- Keep `.env` out of version control and rotate any credentials that have previously been shared.
- Use HTTPS and production OAuth origins only.
- Restrict SMTP sender identities, add SPF/DKIM/DMARC, and comply with applicable email/privacy rules.
- Add rate limits, email audit records, retries/queueing, bounce handling, unsubscribe/suppression checks, and integration tests before production use.
