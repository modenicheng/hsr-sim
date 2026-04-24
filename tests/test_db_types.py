from unittest.mock import MagicMock

from hsr_sim.models.db.types import JSONText


class TestJSONText:
    def test_process_bind_param_with_dict(self):
        json_text = JSONText()
        dialect = MagicMock()
        value = {"key": "value", "num": 123}

        result = json_text.process_bind_param(value, dialect)

        assert result == b'{"key":"value","num":123}'

    def test_process_bind_param_with_list(self):
        json_text = JSONText()
        dialect = MagicMock()
        value = [1, 2, 3]

        result = json_text.process_bind_param(value, dialect)

        assert result == b"[1,2,3]"

    def test_process_bind_param_with_none(self):
        json_text = JSONText()
        dialect = MagicMock()

        result = json_text.process_bind_param(None, dialect)

        assert result is None

    def test_process_bind_param_with_chinese(self):
        json_text = JSONText()
        dialect = MagicMock()
        value = {"name": "中文"}

        result = json_text.process_bind_param(value, dialect)

        assert b"\xe4\xb8\xad\xe6\x96\x87" in result

    def test_process_result_value_with_dict(self):
        json_text = JSONText()
        dialect = MagicMock()
        value = b'{"key":"value","num":123}'

        result = json_text.process_result_value(value, dialect)

        assert result == {"key": "value", "num": 123}

    def test_process_result_value_with_list(self):
        json_text = JSONText()
        dialect = MagicMock()
        value = b"[1,2,3]"

        result = json_text.process_result_value(value, dialect)

        assert result == [1, 2, 3]

    def test_process_result_value_with_none(self):
        json_text = JSONText()
        dialect = MagicMock()

        result = json_text.process_result_value(None, dialect)

        assert result is None
