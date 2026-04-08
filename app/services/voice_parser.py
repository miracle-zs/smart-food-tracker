import calendar
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta

import httpx

from app.config import settings


LOCATION_KEYWORDS = [
    "冰箱冷冻室",
    "冷冻室",
    "冰箱冷藏室",
    "冷藏室",
    "零食柜",
    "橱柜",
]

PRODUCT_KEYWORDS = [
    "鸡柳",
    "鲜牛奶",
    "牛奶",
    "酸奶",
    "鸡蛋",
]

logger = logging.getLogger(__name__)


@dataclass
class ParsedVoiceItem:
    name: str
    location: str
    expiry_date: date
    needs_confirmation: bool


class VoiceParser:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.base_url = base_url if base_url is not None else settings.llm_base_url
        self.model = model if model is not None else settings.llm_model

    def parse(self, raw_text: str) -> ParsedVoiceItem:
        llm_parsed = self._parse_with_llm(raw_text)
        if llm_parsed is not None:
            return llm_parsed

        explicit_date = self._extract_explicit_date(raw_text)
        if explicit_date is None:
            explicit_date = self._extract_fallback_date(raw_text)
        location = self._extract_location(raw_text)
        name = self._extract_name(raw_text)

        if explicit_date:
            return ParsedVoiceItem(
                name=name,
                location=location,
                expiry_date=explicit_date,
                needs_confirmation=False,
            )

        return ParsedVoiceItem(
            name=name,
            location=location,
            expiry_date=date.today() + timedelta(days=30),
            needs_confirmation=True,
        )

    def _extract_explicit_date(self, raw_text: str) -> date | None:
        match = re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_text)
        if not match:
            return None
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))

    def _extract_fallback_date(self, raw_text: str) -> date | None:
        relative_date = self._extract_relative_date(raw_text)
        if relative_date is not None:
            return relative_date

        month_end_date = self._extract_current_year_month_end_date(raw_text)
        if month_end_date is not None:
            return month_end_date

        month_day_date = self._extract_current_year_month_day_date(raw_text)
        if month_day_date is not None:
            return month_day_date

        return None

    def _extract_relative_date(self, raw_text: str) -> date | None:
        relative_offsets = {
            "今天": 0,
            "明天": 1,
            "后天": 2,
        }
        for keyword, offset in relative_offsets.items():
            if keyword in raw_text:
                return date.today() + timedelta(days=offset)

        match = re.search(r"(\d+)天后", raw_text)
        if match:
            return date.today() + timedelta(days=int(match.group(1)))

        return None

    def _extract_current_year_month_end_date(self, raw_text: str) -> date | None:
        match = re.search(r"(?:今年)?(\d{1,2})月底", raw_text)
        if not match:
            return None

        month = int(match.group(1))
        last_day = calendar.monthrange(date.today().year, month)[1]
        return date(date.today().year, month, last_day)

    def _extract_current_year_month_day_date(self, raw_text: str) -> date | None:
        match = re.search(r"(?:今年)?(\d{1,2})月(\d{1,2})[日号]?", raw_text)
        if not match:
            return None

        year = date.today().year
        month = int(match.group(1))
        day = int(match.group(2))
        try:
            return date(year, month, day)
        except ValueError:
            return None

    def _extract_location(self, raw_text: str) -> str:
        for keyword in LOCATION_KEYWORDS:
            if keyword in raw_text:
                return keyword
        return "未指定"

    def _extract_name(self, raw_text: str) -> str:
        for keyword in PRODUCT_KEYWORDS:
            if keyword in raw_text:
                return keyword
        match = re.search(r"(?:一袋|一盒|一瓶|一些)?([\u4e00-\u9fa5]{2,8})", raw_text)
        if match:
            return match.group(1)
        return "未命名食材"

    def _parse_with_llm(self, raw_text: str) -> ParsedVoiceItem | None:
        if not self.api_key or not self.base_url or not self.model:
            return None

        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是一个智能家庭数据提取助手。请从用户的语音输入中提取食物名称、"
                                "存放位置和过期时间。当前日期是："
                                f"{date.today().isoformat()}。请严格以 JSON 格式输出，包含字段："
                                "`name`, `location`, `expiry_date`。"
                            ),
                        },
                        {"role": "user", "content": raw_text},
                    ],
                    "temperature": 0,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return ParsedVoiceItem(
                name=parsed.get("name") or self._extract_name(raw_text),
                location=parsed.get("location") or "未指定",
                expiry_date=date.fromisoformat(parsed["expiry_date"]),
                needs_confirmation=False,
            )
        except Exception:
            logger.exception("LLM voice parsing failed, falling back to local parser")
            return None
