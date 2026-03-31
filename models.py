"""Data models for Hermes HUD."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ── Memory ──────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    text: str
    category: str  # environment, correction, preference, project, todo, other
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.text)


@dataclass
class MemoryState:
    entries: list[MemoryEntry] = field(default_factory=list)
    total_chars: int = 0
    max_chars: int = 0
    source: str = ""  # "memory" or "user"

    @property
    def capacity_pct(self) -> float:
        return (self.total_chars / self.max_chars * 100) if self.max_chars > 0 else 0

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def count_by_category(self) -> dict[str, int]:
        return dict(Counter(e.category for e in self.entries))


# ── Skills ──────────────────────────────────────────────────

@dataclass
class SkillInfo:
    name: str
    category: str
    description: str
    path: str
    modified_at: datetime
    file_size: int = 0
    is_custom: bool = False  # heuristic: modified recently and not in a bulk timestamp


@dataclass
class SkillsState:
    skills: list[SkillInfo] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.skills)

    @property
    def custom_count(self) -> int:
        return sum(1 for s in self.skills if s.is_custom)

    def by_category(self) -> dict[str, list[SkillInfo]]:
        cats: dict[str, list[SkillInfo]] = {}
        for s in self.skills:
            cats.setdefault(s.category, []).append(s)
        return cats

    def category_counts(self) -> dict[str, int]:
        return {k: len(v) for k, v in self.by_category().items()}

    def recently_modified(self, n: int = 5) -> list[SkillInfo]:
        return sorted(self.skills, key=lambda s: s.modified_at, reverse=True)[:n]


# ── Sessions ────────────────────────────────────────────────

@dataclass
class SessionInfo:
    id: str
    source: str  # cli, telegram
    title: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    message_count: int
    tool_call_count: int
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def duration_minutes(self) -> Optional[float]:
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds() / 60
        return None


@dataclass
class DailyStats:
    date: str
    sessions: int
    messages: int
    tool_calls: int
    tokens: int = 0


@dataclass
class SessionsState:
    sessions: list[SessionInfo] = field(default_factory=list)
    daily_stats: list[DailyStats] = field(default_factory=list)
    tool_usage: dict[str, int] = field(default_factory=dict)  # tool_name -> count

    @property
    def total_sessions(self) -> int:
        return len(self.sessions)

    @property
    def total_messages(self) -> int:
        return sum(s.message_count for s in self.sessions)

    @property
    def total_tool_calls(self) -> int:
        return sum(s.tool_call_count for s in self.sessions)

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self.sessions)

    @property
    def date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        if not self.sessions:
            return None, None
        return (
            min(s.started_at for s in self.sessions),
            max(s.started_at for s in self.sessions),
        )

    def by_source(self) -> dict[str, int]:
        return dict(Counter(s.source for s in self.sessions))


# ── Config ──────────────────────────────────────────────────

@dataclass
class ConfigState:
    model: str = ""
    provider: str = ""
    toolsets: list[str] = field(default_factory=list)
    backend: str = ""
    max_turns: int = 0
    compression_enabled: bool = False
    checkpoints_enabled: bool = False


# ── Timeline Events ────────────────────────────────────────

@dataclass
class TimelineEvent:
    timestamp: datetime
    event_type: str  # session, memory_change, skill_modified, config_change, milestone
    title: str
    detail: str = ""
    icon: str = "◆"


# ── Snapshot (for diff tracking) ───────────────────────────

@dataclass
class HUDSnapshot:
    timestamp: datetime
    memory_entry_count: int
    memory_chars: int
    user_entry_count: int
    user_chars: int
    skill_count: int
    custom_skill_count: int
    session_count: int
    total_messages: int
    total_tool_calls: int
    total_tokens: int
    categories: list[str] = field(default_factory=list)


# ── Full HUD State ─────────────────────────────────────────

@dataclass
class HUDState:
    memory: MemoryState = field(default_factory=MemoryState)
    user: MemoryState = field(default_factory=MemoryState)
    skills: SkillsState = field(default_factory=SkillsState)
    sessions: SessionsState = field(default_factory=SessionsState)
    config: ConfigState = field(default_factory=ConfigState)
    timeline: list[TimelineEvent] = field(default_factory=list)
    collected_at: datetime = field(default_factory=datetime.now)
