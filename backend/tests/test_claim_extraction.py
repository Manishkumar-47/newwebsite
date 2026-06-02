from app.services.claim_extraction import ClaimExtractor


def test_rule_based_claim_extraction_finds_statistics_and_dates():
    text = """
    [Page 1]
    India has 900 million internet users. This paragraph is just an opinion.
    ChatGPT launched in 2018. Revenue grew by 14% in 2024.
    """

    claims = ClaimExtractor().extract(text)
    claim_text = [item.claim for item in claims]

    assert any("900 million internet users" in claim for claim in claim_text)
    assert any("ChatGPT launched in 2018" in claim for claim in claim_text)
    assert any("14%" in claim for claim in claim_text)

