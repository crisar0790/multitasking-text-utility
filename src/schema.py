from typing import Any

ALLOWED_ACTIONS = [
    "provide_information",
    "request_more_information",
    "request_more_information",
    "follow_troubleshooting_steps",
    "check_account_details",
    "check_order_status",
    "review_billing",
    "request_refund",
    "escalate_to_human",
    "report_security_issue",
    "no_action_required",
    "other",
]

ALLOWED_TOPICS = [
    "account",
    "billing",
    "technical_support",
    "product_information",
    "orders",
    "returns_and_refunds",
    "complaints",
    "security",
    "other",
]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {
            "type": "string",
            "description": "Concise answer to the user's question.",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence level between 0 and 1.",
            "minimum": 0,
            "maximum": 1,
        },
        "actions": {
            "type": "array",
            "description": (
                "Recommended actions. Use 'no_action_required' when no action "
                "is necessary and 'other' when no predefined action applies."
            ),
            "items": {
                "type": "string",
                "enum": ALLOWED_ACTIONS,
            },
        },
        "topics": {
            "type": "array",
            "description": (
                "Topics detected in the query. User 'other' when the query "
                "does not match any predefined topic."
            ),
            "items": {
                "type": "string",
                "enum": ALLOWED_TOPICS,
            },
        },
        "requires_human_attention": {
            "type": "boolean",
            "description": (
                "Indicates whetger the query should be reviewed "
                "by a human support agent."
            ),
        },
    },
    "required": [
        "answer",
        "confidence",
        "actions",
        "topics",
        "requires_human_attention",
    ],
    "additionalProperties": False,
}

def validate_response(data: Any) -> bool:
    """
    Validates the structure and data types of an assistant response.
    """

    if not isinstance(data, dict):
        return False

    required_fields = {
        "answer",
        "confidence",
        "actions",
        "topics",
        "requires_human_attention",
    }

    if set(data.keys()) != required_fields:
        return False

    if not isinstance(data["answer"], str):
        return False

    if not data["answer"].strip():
        return False

    confidence = data["confidence"]

    # bool must be rejected explicitly because bool is a subclass of int.
    if isinstance(confidence, bool):
        return False

    if not isinstance(confidence, (int, float)):
        return False

    if not 0 <= confidence <= 1:
        return False

    actions = data["actions"]

    if not isinstance(actions, list):
        return False

    if not actions:
        return False

    if not all(action in ALLOWED_ACTIONS for action in actions):
        return False

    topics = data["topics"]

    if not isinstance(topics, list):
        return False

    if not topics:
        return False

    if not all(topic in ALLOWED_TOPICS for topic in topics):
        return False

    if not isinstance(data["requires_human_attention"], bool):
        return False

    # Topics and actions must not contain duplicates.
    if len(set(topics)) != len(topics):
        return False

    if len(set(actions)) != len(actions):
        return False

    # Fallback values must be used alone.
    if "other" in topics and len(topics) > 1:
        return False

    if "other" in actions and len(actions) > 1:
        return False

    if "no_action_required" in actions and len(actions) > 1:
        return False

    # Human attention and escalation must agree.
    requires_human_attention = data["requires_human_attention"]
    has_escalation = "escalate_to_human" in actions

    if requires_human_attention != has_escalation:
        return False

    # Low-confidence responses require human review.
    if confidence < 0.6 and not requires_human_attention:
        return False

    # Security incidents require human review.
    if (
        "report_security_issue" in actions
        and not requires_human_attention
    ):
        return False

    return True
