# Evaluation summary

## Metrics by configuration

| config          | agent   | model    |   runs |   answers |   accuracy_% |   accuracy_in_scope_% |   groundedness_% |   citation_present_% |   correct_refusal_% |   false_refusal_% |   refusals_logged_% |   tool_correct_% |   routing_correct_% |   avg_seconds |   errors |
|:----------------|:--------|:---------|-------:|----------:|-------------:|----------------------:|-----------------:|---------------------:|--------------------:|------------------:|--------------------:|-----------------:|--------------------:|--------------:|---------:|
| multi_qwen3-8b  | multi   | qwen3:8b |      1 |         8 |           75 |                    75 |               75 |                  100 |                 nan |                 0 |                 nan |              100 |                 100 |         233.4 |        0 |
| single_qwen3-8b | single  | qwen3:8b |      1 |         4 |          100 |                   100 |              100 |                  100 |                 100 |                 0 |                 100 |              100 |                     |         112.5 |        0 |

## Accuracy (%) by question category

| category     |   multi_qwen3-8b |   single_qwen3-8b |
|:-------------|-----------------:|------------------:|
| email        |              nan |               100 |
| out_of_scope |              nan |               100 |
| policy       |               75 |               100 |
| schedule     |              nan |               100 |

## Answers that changed between runs (0 question/config pairs)

No answer changed between runs.
