import pytest
from sms_client import PaymentEvent, notify_payment


class FakeClient:
    def send_sms(self, to, template_id, template_vars):
        return {"to": to, "template_id": template_id, "template_vars": template_vars}


def test_high_risk_payment_is_held_before_send():
    event = PaymentEvent("+15550001111", "USD 9.00", "pay-risk", "high")
    with pytest.raises(ValueError, match="manual review"):
        notify_payment(FakeClient(), event, "tpl-1")


def test_normal_payment_hands_template_vars_to_sms():
    event = PaymentEvent("+15550001111", "USD 9.00", "pay-ok", "normal")
    result = notify_payment(FakeClient(), event, "tpl-1")
    assert result["template_vars"]["reference"] == "pay-ok"
