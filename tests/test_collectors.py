from src.parsers.news_parser import infer_category


def test_infer_category_earnings():
    assert infer_category("Q4 earnings and result update") == "earnings"
