from src.evaluation.metrics import counting_accuracy, mae, mape, report


def test_accuracy_perfect():
    assert counting_accuracy(100, 100) == 1.0


def test_accuracy_partial():
    assert counting_accuracy(90, 100) == 0.9


def test_accuracy_over():
    # pred vượt 20% 1 - 0.2 = 0.8
    assert abs(counting_accuracy(120, 100) - 0.8) < 1e-9


def test_mae_mape():
    assert mae([100, 50], [110, 45]) == (10 + 5) / 2
    # (10/110 + 5/45) / 2 * 100
    expected = (10 / 110 + 5 / 45) / 2 * 100
    assert abs(mape([100, 50], [110, 45]) - expected) < 1e-6


def test_report_shape():
    r = report({"motorcycle": 120, "car": 40},
               {"motorcycle": 130, "car": 45, "bus": 3})
    assert r["total_pred"] == 160
    assert r["total_gt"] == 178
    assert "MAPE_percent" in r
    assert "MAE" in r
