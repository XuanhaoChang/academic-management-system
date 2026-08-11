import pytest

from core.constants import score_to_gpa


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (95, (4.0, "A", True)),
        (80, (3.0, "B", True)),
        (60, (1.0, "D", True)),
        (59.9, (0.0, "F", False)),
    ],
)
def test_score_to_gpa(score, expected):
    assert score_to_gpa(score) == expected
