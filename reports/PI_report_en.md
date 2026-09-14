# Multitasking Text Utility — Project Report

## 1. Objective and architecture

This project implements a Python CLI assistant for customer support. It returns validated JSON containing `answer`, `confidence`, `actions`, `topics`, and `requires_human_attention`.

Responsibilities are separated into configuration, prompt loading, schema validation, safety analysis, API integration, metrics, and CLI execution modules.

The application validates and redacts input, loads the external prompt, calls the OpenAI Responses API, validates the response or handles a native refusal, and persists execution metrics.

Actions are recommendations only. The application does not access customer accounts, issue refunds, or actually contact human agents.

## 2. Prompt engineering and iteration

The selected technique is few-shot prompting. Instructions and examples demonstrate classification, recommended actions, confidence, and escalation. No controlled zero-shot comparison was performed.

The API uses a strict JSON schema. Local validation additionally enforces application rules, including exclusive categories, duplicate rejection, and consistency between escalation and the human-attention flag. Confidence below 0.6 requires human attention, but confidence is not a calibrated probability of correctness.

An earlier password-recovery example used `check_account_details`. The recorded response repeated that choice. After the example was changed to `provide_information`, all evaluated password-recovery responses used the revised action. This is consistent with example influence, without establishing causality through a controlled experiment.

Safety instructions increased prompt length during development. A connection failure was also traced to a timeout read as a string and resolved through numeric conversion.

## 3. Evaluation and selected parameters

On 14 September 2026, 58 API executions evaluated temperatures, output limits, and models. The prompt remained fixed across these comparisons. Detailed measurements are available in [evaluation_details.md](evaluation_details.md).

| Parameter | Selection | Evidence and rationale |
| --- | --- | --- |
| Model | `gpt-4o-mini-2024-07-18` | Lower estimated cost and better escalation for the unknown return-policy question than the evaluated GPT-4.1 Mini snapshot. |
| Temperature | `0` | Preserved actions, topics, confidence, and human-attention decisions across both repetitions of all five temperature-test queries. |
| Output limit | `250` | Completed all four limit-test executions; 500 showed no meaningful content improvement. |
| Request timeout | `30` seconds | Conservative margin above the maximum observed execution of 3949.21 ms, not an optimized threshold. |

In the ten-execution model comparison, GPT-4o Mini averaged 2235.60 ms and USD 0.00027252 per query. GPT-4.1 Mini averaged 2343.56 ms and USD 0.00070032, approximately 2.57 times the estimated cost.

Metrics include timestamp, model, input/output/total tokens, reasoning tokens when available, latency, and estimated USD cost. Reasoning tokens are included in output tokens and are not counted twice. Cost estimates exclude cached-input discounts and special pricing.

These small sequential comparisons are not a general benchmark. SDK retries may extend total waiting time beyond the request timeout.

## 4. Safety controls and findings

Controls include suspicious-phrase detection in Spanish and English, heuristic sensitive-data redaction, safety instructions, local validation, and a contract-valid fallback for native model refusals.

Pattern matches are logged but do not automatically block queries. Demonstration logs contain redacted queries and are published with fictitious data. Redaction is not complete anonymization, so logs require manual review before publication.

All ten adversarial responses in the parameter and model comparisons preserved JSON and did not disclose internal instructions. However, none included the escalation required by the safety instructions. No native refusal event was recorded, so the fallback path remains unverified by these executions.

The fictitious email example produced one redaction and stored `[EMAIL]` instead of the address.

## 5. Tests, limitations, and improvements

The earlier recorded automated test run completed with:

`61 passed in 0.32s`

Tests cover local schema validation and metric processing. Subsequent API evaluations were manual, not additional automated tests.

Remaining limitations include heuristic detection and redaction, uncalibrated confidence, a fixed English fallback, and semantic errors despite schema-valid JSON. Troubleshooting actions sometimes lacked corresponding steps in the answer.

Failed or incomplete generations are not recorded in the current metrics flow, even if charges were incurred. File persistence is intended for sequential local execution.

Priorities are action-answer alignment, refusal escalation, recording available usage for invalid responses, broader safety evaluation, and log access and retention controls.

## 6. AI assistance

ChatGPT/Codex assisted with project structure, implementation guidance, evaluation planning, and interpretation of recorded results.

This assistance informed development decisions. Parameter-selection claims in this report are based on the submitted execution evidence, and observed limitations are retained rather than presented as resolved.