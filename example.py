import os
from sms_client import InfraiClient, PaymentEvent, notify_payment


def main() -> None:
    client = InfraiClient()
    client.create_signature("Ledger alerts")
    template = client.create_template(
        "payment-receipt-demo", "Payment {amount} received. Ref {reference}."
    )
    event = PaymentEvent(os.environ["SMS_TO"], "USD 42.00", "pay_8421", "normal")
    result = notify_payment(client, event, str(template["id"]))
    print("payment notification accepted:", result)


if __name__ == "__main__":
    main()
