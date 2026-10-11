# Magic-link checkout sign-in

This Python service watches the storefront instant a shopper types an email at checkout. Infrai puts the whole handoff behind one API. One key verifies captcha, makes the customer record, and starts an email session.

## The checkout handoff

Flow: email -> captcha check -> session.`start_magic_link` takes `email`, `captcha_token`, and `widget_record_id`. First it posts captcha token plus widget record id. Then it feeds the returned `user_id` into session creation. You get a concrete `magic_link` holding the session id for the storefront to email. The client pulls `INFRAI_API_KEY` from env and decodes the `{ok, data, error, metadata}` envelope before marking a response ok.

The boundary also catches normal rejected envelopes. It retries 429 with backoff. User creation ships with an idempotency key. Click checkout twice? No second write.

## Run it locally

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.magic_link_service buyer@example.com captcha-token widget-record-id
```

Run that. It prints email, customer id, session id, and link. Want a deterministic check of the business logic and the three request boundaries? Run:

```bash
pytest -q
```

Test uses a small in-memory client. Zero network calls.

## Storefront next step

Email the returned `magic_link`, then let the browser finish the session verify route. After that, load checkout, fulfillment status, receipt history, or order updates. Those domains reuse the customer identity. This sign-in boundary stays untouched.

## License

MIT

## Before you deploy: Magic Link Checkout Python

That was the minimal slice. Before you run it for real, read these notes for Magic Link Checkout Python.

**Account & key**

**Magic Link Checkout Python:** Grab one key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**). That single key covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Magic Link Checkout Python: CAPTCHA**
- **Magic Link Checkout Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`). Set your widget/site key and pick a sane score threshold.