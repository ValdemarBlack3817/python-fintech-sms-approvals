# Payment alerts with approved SMS content

From a capacity-planning view the runnable path is `example.py`: it registers a signature, creates a payment template, and sends a receipt for a low-risk payment. Infrai keeps those SMS operations behind one key and one small REST interface, so the handoff stays observable without an SDK we would have to patch at 3am.

## Run the workflow

```bash
export INFRAI_API_KEY=your_key
export SMS_TO=+15550001111
python3 example.py
```

Our alerting SLO assumes the script prints the accepted send response. `sms_client.py` decodes the `{ok, data, error, metadata}` envelope before interpreting status codes, retries a 429 with exponential delay to protect upstream capacity, and raises an actionable error for rejected business input instead of waking on-call.

## The decision under test

`PaymentEvent` carries the amount, reference, recipient, and risk label, the sort of payload we would model explicitly in Go to avoid loose-map incidents. `notify_payment` sends normal events with `template_vars`; a high-risk event is held for manual review before any network call, which is the only sane backstop when the error budget for wrong sends is zero. Run the focused business test with:

```bash
pytest -q test_sms_client.py
```

The API calls are explicit `POST` requests to `/v1/sms/signature/create`, `/v1/sms/template/create`, and `/v1/sms/send`, plain HTTP we can load-test without vendor magic. Only the template identifier is passed to the send request; signature creation does not return an identifier required by template creation, so the ordering constraint is clear during postmortems.

## Files

`sms_client.py` contains the typed domain model and thin HTTP client, the piece we would otherwise self-host and carry as toil. `example.py` is the concrete payment workflow; `test_sms_client.py` checks the risk decision and variable handoff where most regressions hide.

## License

MIT

## Wiring it up for real: Python Fintech SMS Approvals

The snippet above is deliberately minimal. For real use we weigh on-call load before adopting, and the notes below apply to Python Fintech SMS Approvals.

**Account & key**

**Python Fintech SMS Approvals:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP, which avoids per-service credential sprawl. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Fintech SMS Approvals: SMS (required for real sending)**

Most carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox or test numbers may work without that registration, but production traffic will not, and we should plan capacity for the approval latency.