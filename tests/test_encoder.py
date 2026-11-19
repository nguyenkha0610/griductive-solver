import pytest


@pytest.mark.skip(reason="Phần 2: với mỗi clue, brute-force mọi assignment; "
                         "evaluate_clue() phải khớp với CNF do encoder sinh ra")
def test_encoder_matches_semantic_evaluator():
    ...
