from app.engine.geocode_helpers import (
    build_address_label,
    build_timeline_label,
    format_route_distance_label,
    parse_leading_house_number,
    result_has_house_number,
)


def test_parse_leading_house_number():
    assert parse_leading_house_number("30 Dương Bá Trạc") == ("30", "Dương Bá Trạc")
    assert parse_leading_house_number("Dương Bá Trạc") == (None, "Dương Bá Trạc")


def test_build_address_label_with_house_number():
    label = build_address_label(
        {
            "housenumber": "30",
            "street": "Dương Bá Trạc",
            "city": "Thành phố Hồ Chí Minh",
        }
    )
    assert label.startswith("30 Dương Bá Trạc")


def test_result_has_house_number():
    assert result_has_house_number("30 Dương Bá Trạc", "30")
    assert not result_has_house_number("Hẻm 301 Dương Bá Trạc", "30")


def test_build_timeline_label():
    label = build_timeline_label(
        {
            "name": "Cầu Nguyễn Văn Cừ",
            "district": "Quận 5",
            "city": "Thành phố Hồ Chí Minh",
        }
    )
    assert label == "Cầu Nguyễn Văn Cừ, Quận 5"


def test_format_route_distance_label():
    assert format_route_distance_label(5.234) == "Km 5.2 trên lộ trình"
