"""Test cơ bản cho line counter — chống đếm trùng khi cùng track_id qua line nhiều lần."""
from src.tracking.counter import Counter, Line


def test_single_crossing():
    line = Line(name="L", p1=(0, 100), p2=(200, 100))
    c = Counter(lines=[line])
    # Track ID 1, class 0 (motorcycle), đi từ (100, 50) → (100, 150) qua line
    c.update(0, [[95, 45, 105, 55]], [1], [0])
    c.update(1, [[95, 145, 105, 155]], [1], [0])
    assert c.counts["L"][0] == 1


def test_no_double_count():
    line = Line(name="L", p1=(0, 100), p2=(200, 100))
    c = Counter(lines=[line])
    # Đi qua rồi quay lại — chỉ đếm 1 lần
    c.update(0, [[95, 45, 105, 55]], [1], [0])
    c.update(1, [[95, 145, 105, 155]], [1], [0])
    c.update(2, [[95, 45, 105, 55]], [1], [0])  # quay lại
    assert c.counts["L"][0] == 1


def test_multi_class():
    line = Line(name="L", p1=(0, 100), p2=(200, 100))
    c = Counter(lines=[line])
    # 2 track khác nhau, 2 class khác nhau, đều qua line
    c.update(0, [[95, 45, 105, 55], [180, 45, 190, 55]], [1, 2], [0, 1])
    c.update(1, [[95, 145, 105, 155], [180, 145, 190, 155]], [1, 2], [0, 1])
    assert c.counts["L"][0] == 1
    assert c.counts["L"][1] == 1
