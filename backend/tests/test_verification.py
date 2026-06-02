from app.services.search import SearchSource
from app.services.verification import VerificationEngine


def test_known_trap_detection_marks_chatgpt_2018_false():
    result = VerificationEngine().verify("ChatGPT launched in 2018.", "date", [])

    assert result["status"] == "FALSE"
    assert "2022" in result["correct_value"]


def test_numeric_fallback_marks_nearby_value_outdated():
    result = VerificationEngine().verify(
        "India has 900 million internet users.",
        "statistic",
        [
            SearchSource(
                title="Telecom report",
                url="https://example.gov/report",
                snippet="India had 954 million internet users according to the latest report.",
                source_type="government",
            )
        ],
    )

    assert result["status"] == "OUTDATED"
    assert result["confidence"] >= 60

