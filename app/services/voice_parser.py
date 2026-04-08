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
ExpiryCandidate = tuple[int, date, tuple[int, int, int]]


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

        location = self._extract_location(raw_text)
        name = self._extract_name(raw_text)

        candidates = self._extract_expiry_candidates(raw_text)
        if candidates:
            expiry_date = self._select_expiry_candidate(candidates)
            return ParsedVoiceItem(
                name=name,
                location=location,
                expiry_date=expiry_date,
                needs_confirmation=False,
            )

        return ParsedVoiceItem(
            name=name,
            location=location,
            expiry_date=date.today() + timedelta(days=30),
            needs_confirmation=True,
        )

    def _extract_explicit_date_candidates(self, raw_text: str | None) -> list[tuple[int, date]]:
        if raw_text is None:
            return []

        candidates: list[tuple[int, date]] = []
        for match in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", raw_text):
            try:
                candidates.append(
                    (
                        match.start(),
                        date(int(match.group(1)), int(match.group(2)), int(match.group(3))),
                    )
                )
            except ValueError:
                continue
        return candidates

    def _extract_expiry_candidates(self, raw_text: str) -> list[ExpiryCandidate]:
        keyword_positions = self._extract_expiry_keyword_positions(raw_text)
        if not keyword_positions:
            return []

        candidates: list[tuple[int, date]] = []
        candidates.extend(self._extract_explicit_date_candidates(raw_text))
        candidates.extend(self._extract_relative_date_candidates(raw_text))
        candidates.extend(self._extract_current_year_month_end_candidates(raw_text))
        candidates.extend(self._extract_current_year_month_day_candidates(raw_text))
        return [(position, value, self._nearest_keyword_distance(position, keyword_positions)) for position, value in candidates]

    def _extract_expiry_keyword_positions(self, raw_text: str) -> list[int]:
        positions: list[int] = []
        for keyword in ("过期", "到期", "截止"):
            positions.extend(match.start() for match in re.finditer(keyword, raw_text))
        return positions

    def _nearest_keyword_distance(self, candidate_position: int, keyword_positions: list[int]) -> tuple[int, int, int]:
        nearest_position = min(keyword_positions, key=lambda position: abs(position - candidate_position))
        return (
            abs(candidate_position - nearest_position),
            0 if candidate_position >= nearest_position else 1,
            candidate_position,
        )

    def _select_expiry_candidate(self, candidates: list[ExpiryCandidate]) -> date:
        return min(candidates, key=lambda candidate: candidate[2])[1]

    def _extract_relative_date_candidates(self, raw_text: str) -> list[tuple[int, date]]:
        candidates: list[tuple[int, date]] = []
        relative_offsets = {
            "今天": 0,
            "明天": 1,
            "后天": 2,
        }

        for keyword, offset in relative_offsets.items():
            for match in re.finditer(keyword, raw_text):
                candidates.append((match.start(), date.today() + timedelta(days=offset)))

        for match in re.finditer(r"(\d+)天后", raw_text):
            candidates.append((match.start(), date.today() + timedelta(days=int(match.group(1)))))

        return candidates

    def _extract_current_year_month_end_candidates(self, raw_text: str) -> list[tuple[int, date]]:
        candidates: list[tuple[int, date]] = []
        year = date.today().year

        for match in re.finditer(r"(?:今年)?(\d{1,2})月底", raw_text):
            month = int(match.group(1))
            try:
                last_day = calendar.monthrange(year, month)[1]
                candidates.append((match.start(), date(year, month, last_day)))
            except (calendar.IllegalMonthError, ValueError):
                continue

        return candidates

    def _extract_current_year_month_day_candidates(self, raw_text: str) -> list[tuple[int, date]]:
        candidates: list[tuple[int, date]] = []
        year = date.today().year

        for match in re.finditer(r"(?:今年)?(\d{1,2})月(\d{1,2})[日号]?", raw_text):
            month = int(match.group(1))
            day = int(match.group(2))
            try:
                candidates.append((match.start(), date(year, month, day)))
            except ValueError:
                continue

        return candidates

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
