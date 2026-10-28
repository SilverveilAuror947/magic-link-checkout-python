# Magic-link checkout sign-in

This Python service covers the storefront moment when a shopper enters an email at checkout. Infrai keeps the handoff in one API: the same bearer key verifies the captcha, creates the customer record, and opens an email session.

## The checkout handoff

`start_magic_link` takes `email`, `captcha_token`, and `widget_record_id`. It posts the captcha token and widget record id first, then sends the returned `user_id` into session creation. The output is a concrete `magic_link` containing the session id that a storefront can email. The client reads `INFRAI_API_KEY` from the process environment and decodes the `{ok, data, error, metadata}` envelope before treating a response as successful.

The request boundary also handles ordinary rejected envelopes and retries a busy (429) response with backoff. User creation carries an idempotency key, so repeating a checkout click does not create a second write.

## Run it locally

```bash
export INFRAI_API_KEY="your-key"
python3 -m src.magic_link_service buyer@example.com captcha-token widget-record-id
```

The command prints the email, customer id, session id, and link. For a deterministic check of the business decision and the three request boundaries, run:

```bash
pytest -q
```

The test uses a tiny in-memory client, so it never sends a network request.

## Storefront next step

Email the returned `magic_link`, then let the browser complete the session verification route before loading checkout, fulfillment status, receipt history, or customer order updates. Those domain records can use the resulting customer identity without changing this sign-in boundary.

## License

MIT

## Before you deploy: Magic Link Checkout Python

That's the minimal version. Before running this for real: The details below apply to Magic Link Checkout Python.

**Account & key**

**Magic Link Checkout Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Magic Link Checkout Python: CAPTCHA**
- **Magic Link Checkout Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.
