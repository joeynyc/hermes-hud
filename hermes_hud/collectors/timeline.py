"""Build a unified timeline of Hermes growth events."""

from __future__ import annotations

from datetime import datetime

from ..models import HUDState, MemoryState, SessionsState, SkillsState, TimelineEvent


def _session_events(sessions: SessionsState) -> list[TimelineEvent]:
    """Generate timeline events from sessions."""
    events = []

    if not sessions.sessions:
        return events

    # First session ever
    sorted_sessions = sorted(sessions.sessions, key=lambda s: s.started_at)
    first = sorted_sessions[0]
    events.append(TimelineEvent(
        timestamp=first.started_at,
        event_type="milestone",
        title="First session",
        detail=f"{first.title or 'Untitled'} via {first.source}",
        icon="★",
    ))

    # Each session as an event
    for s in sorted_sessions:
        events.append(TimelineEvent(
            timestamp=s.started_at,
            event_type="session",
            title=s.title or "Untitled session",
            detail=f"{s.message_count} msgs, {s.tool_call_count} tool calls ({s.source})",
            icon="▸",
        ))

    # Most active day
    if sessions.daily_stats:
        busiest = max(sessions.daily_stats, key=lambda d: d.messages)
        events.append(TimelineEvent(
            timestamp=datetime.strptime(busiest.date, "%Y-%m-%d"),
            event_type="milestone",
            title=f"Most active day: {busiest.date}",
            detail=f"{busiest.sessions} sessions, {busiest.messages} messages, {busiest.tool_calls} tool calls",
            icon="⚡",
        ))

    return events


def _skill_events(skills: SkillsState) -> list[TimelineEvent]:
    """Generate timeline events from skill modifications."""
    events = []

    for skill in skills.skills:
        if skill.is_custom:
            events.append(TimelineEvent(
                timestamp=skill.modified_at,
                event_type="skill_modified",
                title=f"Skill modified: {skill.name}",
                detail=f"Category: {skill.category}",
                icon="⚙",
            ))

    return events


def _memory_events(memory: MemoryState, label: str) -> list[TimelineEvent]:
    """Generate events from memory entries (approximated — no timestamps on individual entries)."""
    events = []

    corrections = [e for e in memory.entries if e.category == "correction"]
    if corrections:
        events.append(TimelineEvent(
            timestamp=datetime.now(),  # we don't have per-entry timestamps
            event_type="memory_change",
            title=f"{len(corrections)} corrections stored in {label}",
            detail="; ".join(c.text[:60] + "..." for c in corrections[:3]),
            icon="✦",
        ))

    return events


def build_timeline(state: HUDState) -> list[TimelineEvent]:
    """Build a unified, sorted timeline from all data sources."""
    events = []

    events.extend(_session_events(state.sessions))
    events.extend(_skill_events(state.skills))
    events.extend(_memory_events(state.memory, "memory"))
    events.extend(_memory_events(state.user, "user profile"))

    # Sort by timestamp
    events.sort(key=lambda e: e.timestamp)

    return events
