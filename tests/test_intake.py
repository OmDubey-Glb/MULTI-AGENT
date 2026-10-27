import pytest
from fastapi import HTTPException

from app.agents import intake


@pytest.fixture(autouse=True)
def clean_intake_state():
    intake._sessions.clear()
    intake._dev_inbox.clear()
    intake._requests.clear()


def make_verified_session():
    start = intake.OtpStart(
        customer_id="CUST-1001",
        channel="email",
        destination="asha@example.com",
    )
    created = intake.start_otp(start)
    code = intake.inbox()[0]["code"]
    intake.verify_otp(intake.OtpVerify(session_id=created["session_id"], code=code))
    return created["session_id"]


def test_otp_is_available_only_in_dev_inbox_and_verifies():
    created = intake.start_otp(intake.OtpStart(
        customer_id="CUST-1001", channel="email", destination="asha@example.com"
    ))
    message = intake.inbox()[0]
    assert created["delivery"] == "OFFLINE_DEV_INBOX"
    assert len(message["code"]) == 6
    assert intake.verify_otp(intake.OtpVerify(
        session_id=created["session_id"], code=message["code"]
    ))["verified"] is True


def test_request_requires_verified_otp_and_preserves_selected_scope():
    session_id = make_verified_session()
    result = intake.submit_request(intake.RequestSubmit(
        session_id=session_id,
        categories=["profile_identity", "contact_details"],
    ))
    assert result["selected_categories"] == ["profile_identity", "contact_details"]
    assert result["status"] == "RECEIVED"
    assert result["policy_assessment"] == {
        "profile_identity": "DELETE",
        "contact_details": "DELETE",
    }


def test_verified_session_cannot_submit_twice():
    session_id = make_verified_session()
    payload = intake.RequestSubmit(
        session_id=session_id, categories=["profile_identity"]
    )
    intake.submit_request(payload)
    with pytest.raises(HTTPException) as error:
        intake.submit_request(payload)
    assert error.value.status_code == 409


def test_invalid_category_is_rejected():
    session_id = make_verified_session()
    with pytest.raises(HTTPException) as error:
        intake.submit_request(intake.RequestSubmit(
            session_id=session_id, categories=["not_a_real_category"]
        ))
    assert error.value.status_code == 422
