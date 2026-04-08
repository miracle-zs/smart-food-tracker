from datetime import date

from app.services.voice_parser import VoiceParser


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_voice_parser_uses_llm_when_configured(monkeypatch):
    parser = VoiceParser(
        api_key="test-key",
        base_url="https://example.com",
        model="demo-model",
    )

    def fake_post(url, json, headers, timeout):
        assert url == "https://example.com/chat/completions"
        assert json["model"] == "demo-model"
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                '{"name":"鸡柳","location":"冷冻室",'
                                '"expiry_date":"2026-10-31"}'
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.voice_parser.httpx.post", fake_post)

    parsed = parser.parse("今天放了一袋鸡柳在冷冻室，今年10月底过期")

    assert parsed.name == "鸡柳"
    assert parsed.location == "冷冻室"
    assert parsed.expiry_date == date(2026, 10, 31)
    assert parsed.needs_confirmation is False
