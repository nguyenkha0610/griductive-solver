import pytest
from griductive.solver.dpll import solve


@pytest.mark.skip(reason="Phần 3: bỏ skip khi cài xong")
def test_sat_and_unsat():
    assert solve([[1, 2], [-1, 2]], 2).sat
    assert not solve([[1], [-1]], 1).sat
    assert not solve([[1, 2], [-1, 2]], 2, assumptions=[-2]).sat   # ví dụ trong đề
