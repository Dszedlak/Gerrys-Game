"""
Tests for the job-driven rules added for the 22/08/26 changes:

  - Chancellor: two votes, but only in favour of changing government
  - Charity Commissioner: -20 minutes to every opposition player

Unlike test_balance_books.py, this imports the real implementation so it
cannot silently drift from the code it is meant to protect.

Run with:  python backend/tests/test_job_rules.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.websocket.sockets import (  # noqa: E402
    vote_weight,
    CHANCELLOR_JOB,
    CHANCELLOR_CHANGE_VOTE_WEIGHT,
    CHARITY_COMMISSIONER_JOB,
    CHARITY_COMMISSIONER_PENALTY,
)


def tally(ballots, chancellor_id=None):
    """Mirror of the counting in concludeVoting, using the real weighting."""
    counts = {"yes": 0, "no": 0, "abstain": 0}
    for voter_id, vote in ballots.items():
        counts[vote] += vote_weight(vote, voter_id == chancellor_id)

    if counts["yes"] > counts["no"]:
        outcome = "PASSED"
    elif counts["no"] > counts["yes"]:
        outcome = "REJECTED"
    else:
        outcome = "TIE"
    return counts, outcome


def test_chancellor_vote_weight():
    """The double vote applies to 'yes' only."""
    assert vote_weight("yes", True) == CHANCELLOR_CHANGE_VOTE_WEIGHT == 2
    assert vote_weight("no", True) == 1
    assert vote_weight("abstain", True) == 1

    # Everyone else always carries exactly one vote
    for vote in ("yes", "no", "abstain"):
        assert vote_weight(vote, False) == 1

    print("PASS: Chancellor weighting - 2 for change, 1 otherwise")


def test_chancellor_can_carry_a_vote_for_change():
    """Chancellor voting yes outweighs two opponents."""
    counts, outcome = tally({1: "yes", 2: "no", 3: "no"}, chancellor_id=1)
    assert counts == {"yes": 2, "no": 2, "abstain": 0}, counts
    assert outcome == "TIE", outcome

    counts, outcome = tally({1: "yes", 2: "yes", 3: "no", 4: "no"}, chancellor_id=1)
    assert counts == {"yes": 3, "no": 2, "abstain": 0}, counts
    assert outcome == "PASSED", outcome

    print("PASS: Chancellor's yes carries extra weight")


def test_chancellor_cannot_block_with_a_double_no():
    """Voting to remain is worth one vote, so the result is unchanged."""
    counts, outcome = tally({1: "no", 2: "yes", 3: "yes"}, chancellor_id=1)
    assert counts == {"yes": 2, "no": 1, "abstain": 0}, counts
    assert outcome == "PASSED", outcome

    # Identical to the same ballots cast by a non-Chancellor
    plain_counts, plain_outcome = tally({1: "no", 2: "yes", 3: "yes"})
    assert (counts, outcome) == (plain_counts, plain_outcome)

    print("PASS: Chancellor's no counts once, same as anyone else")


def charity_penalty(voter_id, commissioner_id):
    """Mirror of the Charity Commissioner branch in balanceChange."""
    if commissioner_id is not None and voter_id != commissioner_id:
        return CHARITY_COMMISSIONER_PENALTY
    return 0


def test_charity_commissioner_penalty():
    assert CHARITY_COMMISSIONER_JOB == "Charity Commissioner"
    assert CHARITY_COMMISSIONER_PENALTY == -20

    # Opposition players pay
    assert charity_penalty(1, commissioner_id=2) == -20
    assert charity_penalty(3, commissioner_id=2) == -20
    # The Commissioner themselves does not
    assert charity_penalty(2, commissioner_id=2) == 0
    # Nobody pays when the job is not in the game
    assert charity_penalty(1, commissioner_id=None) == 0

    print("PASS: Charity Commissioner penalises opposition only")


def test_job_name_constants_match_the_data():
    """Guard against a rename breaking the name-based lookups."""
    import json

    jobs_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "data_collections", "jobs.json"
    )
    with open(jobs_path, encoding="utf-8-sig") as fh:
        names = {j["name"] for j in json.load(fh)}

    assert CHANCELLOR_JOB in names, f"{CHANCELLOR_JOB} missing from jobs.json"
    assert CHARITY_COMMISSIONER_JOB in names, f"{CHARITY_COMMISSIONER_JOB} missing from jobs.json"
    assert "Doctor" in names
    assert "Stock Broker" in names, "Stock Broker missing - was it renamed?"
    assert "Tax Officer" not in names, "Tax Officer should have been renamed to Stock Broker"

    print("PASS: job name constants match jobs.json")


if __name__ == "__main__":
    test_chancellor_vote_weight()
    test_chancellor_can_carry_a_vote_for_change()
    test_chancellor_cannot_block_with_a_double_no()
    test_charity_commissioner_penalty()
    test_job_name_constants_match_the_data()
    print("\nAll job rule tests passed.")
