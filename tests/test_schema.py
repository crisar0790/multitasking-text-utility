from copy import deepcopy

import pytest

from src.schema import validate_response


@pytest.fixture
def valid_response():
    """
    Returns a valid response for testing.
    """

    return {
        "answer": "Please restart the application.",
        "confidence": 0.9,
        "actions": [
            "follow_troubleshooting_steps"
        ],
        "topics": [
            "technical_support"
        ],
        "requires_human_attention": False,
    }


def test_accepts_valid_response(valid_response):
    assert validate_response(valid_response) is True


@pytest.mark.parametrize(
    "field",
    [
        "answer",
        "confidence",
        "actions",
        "topics",
        "requires_human_attention",
    ],
)
def test_rejects_missing_fields(valid_response, field):
    response = deepcopy(valid_response)
    del response[field]

    assert validate_response(response) is False


def test_rejects_extra_fields(valid_response):
    response = deepcopy(valid_response)
    response["unexpected_field"] = "unexpected value"

    assert validate_response(response) is False


@pytest.mark.parametrize(
    "confidence",
    [
        -0.1,
        1.1,
        "0.9",
        True,
        None,
    ],
)
def test_rejects_invalid_confidence(
    valid_response,
    confidence,
):
    response = deepcopy(valid_response)
    response["confidence"] = confidence

    assert validate_response(response) is False


@pytest.mark.parametrize(
    "actions",
    [
        [],
        ["invalid_action"],
        [123],
        "provide_information",
        None,
    ],
)
def test_rejects_invalid_actions(valid_response, actions):
    response = deepcopy(valid_response)
    response["actions"] = actions

    assert validate_response(response) is False


@pytest.mark.parametrize(
    "topics",
    [
        [],
        ["invalid_topic"],
        [123],
        "technical_support",
        None,
    ],
)
def test_rejects_invalid_topics(valid_response, topics):
    response = deepcopy(valid_response)
    response["topics"] = topics

    assert validate_response(response) is False


@pytest.mark.parametrize(
    "answer",
    [
        "",
        "   ",
        123,
        None,
    ],
)
def test_rejects_invalid_answer(valid_response, answer):
    response = deepcopy(valid_response)
    response["answer"] = answer

    assert validate_response(response) is False


@pytest.mark.parametrize(
    "requires_human_attention",
    [
        "true",
        1,
        None,
    ],
)
def test_rejects_invalid_human_attention(
    valid_response,
    requires_human_attention,
):
    response = deepcopy(valid_response)
    response["requires_human_attention"] = (
        requires_human_attention
    )

    assert validate_response(response) is False


def test_accepts_other_topic(valid_response):
    response = deepcopy(valid_response)
    response["topics"] = ["other"]

    assert validate_response(response) is True

@pytest.mark.parametrize(
    "field, values",
    [
        (
            "topics",
            ["technical_support", "technical_support"],
        ),
        (
            "actions",
            [
                "follow_troubleshooting_steps",
                "follow_troubleshooting_steps",
            ],
        ),
        (
            "topics",
            ["other", "account"],
        ),
        (
            "actions",
            ["other", "provide_information"],
        ),
        (
            "actions",
            [
                "no_action_required",
                "provide_information",
            ],
        ),
    ],
)
def test_rejects_invalid_combinations(
    valid_response,
    field,
    values,
):
    response = deepcopy(valid_response)
    response[field] = values

    assert validate_response(response) is False


def test_rejects_escalation_without_human_attention(
    valid_response,
):
    response = deepcopy(valid_response)
    response["actions"] = ["escalate_to_human"]

    assert validate_response(response) is False


def test_rejects_human_attention_without_escalation(
    valid_response,
):
    response = deepcopy(valid_response)
    response["requires_human_attention"] = True

    assert validate_response(response) is False


def test_accepts_consistent_escalation(valid_response):
    response = deepcopy(valid_response)
    response["actions"] = [
        "review_billing",
        "escalate_to_human",
    ]
    response["requires_human_attention"] = True

    assert validate_response(response) is True


def test_rejects_low_confidence_without_escalation(
    valid_response,
):
    response = deepcopy(valid_response)
    response["confidence"] = 0.5

    assert validate_response(response) is False


def test_accepts_low_confidence_with_escalation(
    valid_response,
):
    response = deepcopy(valid_response)
    response["confidence"] = 0.5
    response["actions"] = ["escalate_to_human"]
    response["requires_human_attention"] = True

    assert validate_response(response) is True


def test_accepts_confidence_at_threshold(valid_response):
    response = deepcopy(valid_response)
    response["confidence"] = 0.6

    assert validate_response(response) is True


def test_rejects_security_incident_without_escalation(
    valid_response,
):
    response = deepcopy(valid_response)
    response["topics"] = ["security"]
    response["actions"] = ["report_security_issue"]

    assert validate_response(response) is False


def test_accepts_security_incident_with_escalation(
    valid_response,
):
    response = deepcopy(valid_response)
    response["topics"] = ["security"]
    response["actions"] = [
        "report_security_issue",
        "escalate_to_human",
    ]
    response["requires_human_attention"] = True

    assert validate_response(response) is True