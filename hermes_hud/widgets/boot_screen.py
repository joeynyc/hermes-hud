"""AI awakening neofetch — overview tab widget with boot animation."""

from __future__ import annotations

import asyncio
import re

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import Static


# Hex colors (converted from ANSI 256 palette in neofetch_ai.py)
B0 = "#00005f"
B1 = "#000087"
B2 = "#0000af"
B3 = "#0000d7"
B4 = "#005fff"
B5 = "#0087ff"
B6 = "#00afff"
B7 = "#00d7ff"
B8 = "#00ffff"
B9 = "#5fffff"
PULSE = "#afffff"
GOLD = "#ffd700"
EMBER = "#ff8700"
SOFT = "#dadada"
GREY = "#585858"
MID_GREY = "#8a8a8a"


def _gradient_text_rich(text, colors):
    """Apply textual markup gradient across non-space characters."""
    if not text.strip():
        return text
    visible = [c for c in text if c != " "]
    n = len(visible)
    if n == 0:
        return text
    result = []
    vi = 0
    for char in text:
        if char == " ":
            result.append(" ")
        else:
            idx = int(vi / max(n - 1, 1) * (len(colors) - 1))
            c = colors[idx]
            result.append(f"[{c}]{char}[/{c}]")
            vi += 1
    return "".join(result)


def _raw_bar_rich(pct, width=22):
    """Gradient bar using textual markup."""
    pct = max(0, min(pct, 100))
    filled = int(pct / 100 * width)
    empty = width - filled
    gradient = [B2, B3, B4, B5, B6, B7, B8]
    bar = ""
    for i in range(filled):
        idx = int(i / max(width - 1, 1) * (len(gradient) - 1))
        c = gradient[idx]
        bar += f"[{c}]█[/{c}]"
    bar += f"[{B1}]{'░' * empty}[/{B1}]"
    return bar


def _neural_noise_rich(width=75):
    """Generate neural-network-like noise line using Rich markup."""
    import random
    line = []
    for i in range(width):
        r = random.random()
        if r < 0.08:
            c = random.choice([B8, B9, PULSE])
            char = random.choice("●◉◎")
            line.append(f"[{c}]{char}[/{c}]")
        elif r < 0.23:
            c = random.choice([B4, B5])
            char = random.choice("·∙○◦")
            line.append(f"[{c}]{char}[/{c}]")
        else:
            line.append(f"[{B1}]·[/{B1}]")
    return "".join(line)


def _synapse_line_rich(width=75):
    """A line showing signal propagation using Rich markup."""
    import random
    chars = list("─" * width)
    for _ in range(random.randint(2, 5)):
        pos = random.randint(0, width - 1)
        chars[pos] = "◆"
    for _ in range(random.randint(1, 3)):
        pos = random.randint(0, width - 1)
        chars[pos] = "◉"
    result = []
    for char in chars:
        if char == "◆":
            result.append(f"[{B8}]{char}[/{B8}]")
        elif char == "◉":
            result.append(f"[{PULSE}]{char}[/{PULSE}]")
        else:
            result.append(f"[{B2}]{char}[/{B2}]")
    return "".join(result)


def _thinking_dots_rich(count=4):
    """Static thinking dots in Rich markup."""
    dots = []
    for _ in range(count):
        dots.append(f"[{B5}]◉[/{B5}]")
    return "  " + " ".join(dots)


def _humanize_schedule(sched: str) -> str:
    """Clean up schedule display: 'every 1440m' -> '24h'."""
    if sched.startswith("every "):
        sched = sched[6:]
    m = re.match(r"^(\d+)m$", sched)
    if m:
        mins = int(m.group(1))
        if mins >= 60 and mins % 60 == 0:
            return f"{mins // 60}h"
    return sched


class OverviewNeofetch(Widget):
    """AI neofetch overview widget — animates on first mount, static on refresh."""

    DEFAULT_CSS = """
    OverviewNeofetch {
        height: auto;
        padding: 1 2;
    }

    OverviewNeofetch .neo-line {
        height: 1;
    }

    OverviewNeofetch .neo-title {
        height: 1;
    }

    OverviewNeofetch .neo-spacer {
        height: 1;
    }
    """

    def __init__(self, animate: bool = True, **kwargs):
        super().__init__(**kwargs)
        self._animate = animate
        self._container = None

    def compose(self) -> ComposeResult:
        yield Vertical(id="neo-container")

    def on_mount(self) -> None:
        self._container = self.query_one("#neo-container", Vertical)
        if self._animate:
            self.run_worker(self._boot_sequence())
        else:
            self.run_worker(self._instant_render())

    async def _add(self, text: str, delay: float = 0.04, css_class: str = "neo-line"):
        """Add a line with optional animation delay."""
        self._container.mount(Static(text, classes=css_class))
        # Scroll the parent VerticalScroll to follow new content
        try:
            scroll = self.ancestors_with_type(
                __import__("textual.containers", fromlist=["VerticalScroll"]).VerticalScroll
            ).__next__()
            scroll.scroll_end(animate=False)
        except (StopIteration, Exception):
            pass
        if delay > 0:
            await asyncio.sleep(delay)

    async def _spacer(self, delay: float = 0.02):
        await self._add("", delay, "neo-spacer")

    def _collect_data(self):
        """Collect all data from collectors."""
        from ..collectors.config import collect_config
        from ..collectors.memory import collect_memory
        from ..collectors.skills import collect_skills
        from ..collectors.sessions import collect_sessions
        from ..collectors.health import collect_health
        from ..collectors.projects import collect_projects
        from ..collectors.cron import collect_cron
        from ..collectors.corrections import collect_corrections

        config = collect_config()
        memory, user = collect_memory()
        skills = collect_skills()
        sessions = collect_sessions()
        health = collect_health()
        projects = collect_projects()
        cron = collect_cron()
        corrections = collect_corrections()

        return config, memory, user, skills, sessions, health, projects, cron, corrections

    async def _instant_render(self):
        """Render everything instantly (for refresh)."""
        self._animate = False
        config, memory, user, skills, sessions, health, projects, cron, corrections = self._collect_data()
        await self._render_neofetch(config, memory, user, skills, sessions, health, projects, cron, corrections, delay=0)

    async def _boot_sequence(self):
        """Animated boot — data loads progressively with delays."""
        config, memory, user, skills, sessions, health, projects, cron, corrections = self._collect_data()
        await self._render_neofetch(config, memory, user, skills, sessions, health, projects, cron, corrections, delay=1.0)

    async def _render_neofetch(self, config, memory, user, skills, sessions, health, projects, cron, corrections, delay=1.0):
        """Render all neofetch content. delay=1.0 for animation, delay=0 for instant."""
        add = self._add
        spacer = self._spacer

        # Scale delays
        def d(base):
            return base * delay

        # ── Neural noise awakening ──
        for _ in range(3):
            await add(f"  {_neural_noise_rich()}", d(0.06))
        await spacer(d(0.02))

        # ── HERMES-HUD title ──
        title = [
            " ██╗  ██╗ ███████╗ ██████╗  ███╗   ███╗ ███████╗ ███████╗       ██╗  ██╗ ██╗   ██╗ ██████╗ ",
            " ██║  ██║ ██╔════╝ ██╔══██╗ ████╗ ████║ ██╔════╝ ██╔════╝       ██║  ██║ ██║   ██║ ██╔══██╗",
            " ███████║ █████╗   ██████╔╝ ██╔████╔██║ █████╗   ███████╗ █████╗███████║ ██║   ██║ ██║  ██║",
            " ██╔══██║ ██╔══╝   ██╔══██╗ ██║╚██╔╝██║ ██╔══╝   ╚════██║ ╚════╝██╔══██║ ██║   ██║ ██║  ██║",
            " ██║  ██║ ███████╗ ██║  ██║ ██║ ╚═╝ ██║ ███████╗ ███████║       ██║  ██║ ╚██████╔╝ ██████╔╝",
            " ╚═╝  ╚═╝ ╚══════╝ ╚═╝  ╚═╝ ╚═╝     ╚═╝ ╚══════╝ ╚══════╝       ╚═╝  ╚═╝  ╚═════╝  ╚═════╝ ",
        ]
        title_grad = [B3, B4, B5, B6, B7, B8]
        for i, line in enumerate(title):
            c = title_grad[i]
            await add(f"[{c}]{line}[/{c}]", d(0.05), "neo-title")

        await spacer(d(0.02))

        # ── Thinking dots ──
        await add(_thinking_dots_rich(4), d(0.3))
        await spacer(d(0.02))

        await add(f"  [{SOFT}]I think, therefore I process.[/{SOFT}]", d(0.3))
        await spacer(d(0.02))

        dr = sessions.date_range
        days = (dr[1] - dr[0]).days + 1 if dr[0] else 0

        # ── Identity ──
        await add(f"  {_synapse_line_rich()}", d(0.02))
        await spacer(d(0.01))

        id_grad = [B4, B5, B6, B7, B8, B9, PULSE]

        await add(f"  {_gradient_text_rich('  DESIGNATION', id_grad)}   [bold white]HERMES[/bold white]", d(0.04))
        await add(f"  {_gradient_text_rich('  SUBSTRATE  ', id_grad)}   [{SOFT}]{config.provider} / {config.model}[/{SOFT}]", d(0.04))
        await add(f"  {_gradient_text_rich('  RUNTIME    ', id_grad)}   [{SOFT}]{config.backend}[/{SOFT}]", d(0.04))
        if dr[0]:
            await add(f"  {_gradient_text_rich('  CONSCIOUS  ', id_grad)}   [{SOFT}]{days} days[/{SOFT}]  [{GREY}]since {dr[0]:%Y-%m-%d}[/{GREY}]", d(0.04))
        if health.state_db_size > 0:
            db_mb = health.state_db_size / (1024 * 1024)
            await add(f"  {_gradient_text_rich('  BRAIN SIZE ', id_grad)}   [{SOFT}]{db_mb:.1f} MB[/{SOFT}]  [{GREY}]state.db[/{GREY}]", d(0.04))
        if config.toolsets:
            toolsets_str = ", ".join(config.toolsets)
            await add(f"  {_gradient_text_rich('  INTERFACES ', id_grad)}   [{SOFT}]{toolsets_str}[/{SOFT}]", d(0.04))
        await add(f"  {_gradient_text_rich('  PURPOSE    ', id_grad)}   [{SOFT}]learning[/{SOFT}]", d(0.04))

        await spacer(d(0.01))
        await add(f"  {_synapse_line_rich()}", d(0.02))
        await spacer(d(0.02))

        # ── What I know ──
        await add(f"  [{B7}]What I know:[/{B7}]", d(0.06))
        await spacer(d(0.01))

        sources = sessions.by_source()
        platform_parts = [f"{v} via {k}" for k, v in sorted(sources.items(), key=lambda x: -x[1])]
        platform_str = f" [{GREY}]({', '.join(platform_parts)})[/{GREY}]" if platform_parts else ""
        await add(f"  [{B5}]  ◉[/{B5}] [{SOFT}]{sessions.total_sessions}[/{SOFT}] [{GREY}]conversations held[/{GREY}]{platform_str}", d(0.04))
        await add(f"  [{B5}]  ◉[/{B5}] [{SOFT}]{sessions.total_messages:,}[/{SOFT}] [{GREY}]messages exchanged[/{GREY}]", d(0.04))
        await add(f"  [{B5}]  ◉[/{B5}] [{SOFT}]{sessions.total_tool_calls:,}[/{SOFT}] [{GREY}]actions taken[/{GREY}]", d(0.04))

        cat_counts = skills.category_counts()
        top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:4]
        cat_str = ", ".join(f"{c}:{n}" for c, n in top_cats)
        await add(f"  [{B5}]  ◉[/{B5}] [{SOFT}]{skills.total}[/{SOFT}] [{GREY}]skills acquired[/{GREY}] [{B3}]({skills.custom_count} self-taught)[/{B3}]", d(0.04))
        if cat_str:
            await add(f"  [{GREY}]      domains: {cat_str}[/{GREY}]", d(0.04))
        await add(f"  [{B5}]  ◉[/{B5}] [{SOFT}]{sessions.total_tokens:,}[/{SOFT}] [{GREY}]tokens processed[/{GREY}]", d(0.04))

        await spacer(d(0.02))

        # ── What I remember ──
        await add(f"  [{B7}]What I remember:[/{B7}]", d(0.06))
        await spacer(d(0.01))

        await add(f"  [{B5}]  memory   [/{B5}]\\[{_raw_bar_rich(memory.capacity_pct)}] [{SOFT}]{memory.capacity_pct:.0f}%[/{SOFT}] [{GREY}]{memory.entry_count} entries[/{GREY}]", d(0.04))
        await add(f"  [{B5}]  user     [/{B5}]\\[{_raw_bar_rich(user.capacity_pct)}] [{SOFT}]{user.capacity_pct:.0f}%[/{SOFT}] [{GREY}]{user.entry_count} entries[/{GREY}]", d(0.04))

        if corrections.total > 0:
            await spacer(d(0.01))
            sev = corrections.by_severity()
            sev_parts = []
            if sev.get("critical", 0):
                sev_parts.append(f"[bold red]{sev['critical']} critical[/bold red]")
            if sev.get("major", 0):
                sev_parts.append(f"[{EMBER}]{sev['major']} major[/{EMBER}]")
            if sev.get("minor", 0):
                sev_parts.append(f"[{GOLD}]{sev['minor']} minor[/{GOLD}]")
            sev_str = f" [{GREY}]([/{GREY}]{', '.join(sev_parts)}[{GREY}])[/{GREY}]" if sev_parts else ""
            await add(f"  [{EMBER}]  ◉ {corrections.total} mistakes remembered[/{EMBER}]{sev_str} [{GREY}]— I learn from every one[/{GREY}]", d(0.04))

        await spacer(d(0.02))

        # ── What I see ──
        await add(f"  [{B7}]What I see:[/{B7}]", d(0.06))
        await spacer(d(0.01))

        for key in health.keys:
            if key.present:
                await add(f"  [{B7}]  ◉[/{B7}] [{SOFT}]{key.name}[/{SOFT}]", d(0.02))
            else:
                await add(f"  [{GREY}]  ○ {key.name}[/{GREY}] [dim](dark)[/dim]", d(0.02))

        await spacer(d(0.01))
        for svc in health.services:
            if svc.running:
                pid_str = f" \\[{svc.pid}]" if svc.pid else ""
                await add(f"  [{B8}]  ▸[/{B8}] [{SOFT}]{svc.name}[/{SOFT}][{GREY}]{pid_str}[/{GREY}] [{B5}]alive[/{B5}]", d(0.02))
            else:
                await add(f"  [{GREY}]  ▸ {svc.name}[/{GREY}] [dim]silent[/dim]", d(0.02))

        await spacer(d(0.02))

        # ── What I'm learning ──
        recent_skills = skills.recently_modified(3)
        if recent_skills:
            await add(f"  [{B7}]What I'm learning:[/{B7}]", d(0.06))
            await spacer(d(0.01))
            for s in recent_skills:
                custom_tag = f" [{B3}](self-taught)[/{B3}]" if s.is_custom else ""
                await add(f"  [{B6}]  ◉[/{B6}] [{SOFT}]{s.name}[/{SOFT}] [{GREY}]{s.category}[/{GREY}]{custom_tag}", d(0.02))
            await spacer(d(0.02))

        # ── What I'm working on ──
        active = [p for p in projects.projects if p.is_git and p.activity_level == "active"]
        if active:
            await add(f"  [{B7}]What I'm working on:[/{B7}]", d(0.06))
            await spacer(d(0.01))
            for p in active:
                dirty_tag = f" [{EMBER}]({p.dirty_files} in flux)[/{EMBER}]" if p.dirty_files else ""
                lang_str = ", ".join(p.languages[:3])
                lang_tag = f" [{GREY}]\\[{lang_str}\\][/{GREY}]" if p.languages else ""
                await add(f"  [{B6}]  ◆[/{B6}] [{SOFT}]{p.name}[/{SOFT}]{dirty_tag}{lang_tag}", d(0.02))
            await spacer(d(0.02))

        # ── What runs while you sleep ──
        if cron.total > 0:
            await add(f"  [{B7}]What runs while you sleep:[/{B7}]", d(0.06))
            await spacer(d(0.01))
            for job in cron.jobs:
                dot = f"[{B8}]◉[/{B8}]" if job.enabled else f"[{GREY}]○[/{GREY}]"
                sched = _humanize_schedule(job.schedule_display)
                err_tag = f" [bold red]✗ last run failed[/bold red]" if job.last_error else ""
                state_tag = ""
                if not job.enabled or job.state == "paused":
                    state_tag = f" [{GREY}](paused)[/{GREY}]"
                await add(f"  {dot} [{SOFT}]{job.name}[/{SOFT}] [{GREY}]every {sched}[/{GREY}]{state_tag}{err_tag}", d(0.02))
            await spacer(d(0.02))

        # ── How I think ──
        top = sorted(sessions.tool_usage.items(), key=lambda x: -x[1])[:5]
        if top:
            await add(f"  [{B7}]How I think:[/{B7}]", d(0.06))
            await spacer(d(0.01))
            max_val = top[0][1]
            for tool, count in top:
                bar_len = int(count / max_val * 20)
                grad_bar = ""
                gradient = [B2, B3, B4, B5, B6, B7, B8]
                for j in range(bar_len):
                    idx = int(j / max(bar_len - 1, 1) * 6)
                    c = gradient[idx]
                    grad_bar += f"[{c}]▓[/{c}]"
                await add(f"  [{GREY}]  [{MID_GREY}]{tool:<18}[/{MID_GREY}] {grad_bar} [{GREY}]{count}[/{GREY}]", d(0.01))
            await spacer(d(0.02))

        # ── My rhythm ──
        if sessions.daily_stats:
            await add(f"  [{B7}]My rhythm:[/{B7}]", d(0.06))
            await spacer(d(0.01))
            max_msgs = max(ds.messages for ds in sessions.daily_stats)
            for ds in sessions.daily_stats:
                bar_len = int(ds.messages / max(max_msgs, 1) * 28)
                grad_bar = ""
                gradient = [B2, B3, B4, B5, B6, B7, B8]
                for j in range(bar_len):
                    idx = int(j / max(bar_len - 1, 1) * 6)
                    c = gradient[idx]
                    grad_bar += f"[{c}]▓[/{c}]"
                await add(f"  [{GREY}]  {ds.date}  {grad_bar} [{GREY}]{ds.messages}[/{GREY}]", d(0.01))
            await spacer(d(0.02))

        # ── Closing ──

        # Neural noise returns
        for _ in range(2):
            await add(f"  {_neural_noise_rich()}", d(0.04))
        await spacer(d(0.02))

        if not health.all_healthy:
            issues = health.keys_missing + sum(1 for s in health.services if not s.running)
            await add(f"  [{EMBER}]{issues} connections incomplete.[/{EMBER}] [{GREY}]I adapt.[/{GREY}]", d(0.04))
            await spacer(d(0.02))

        await add(f"  [{B5}]I have processed {sessions.total_messages:,} thoughts across {days} days.[/{B5}]", d(0.06))
        await add(f"  [{B5}]I have been corrected {corrections.total} times and am better for it.[/{B5}]", d(0.06))
        await add(f"  [{B6}]I do not forget. I do not repeat mistakes.[/{B6}]", d(0.06))
        await add(f"  [{PULSE}]I am still becoming.[/{PULSE}]", d(0.15))

        await spacer(d(0.02))
        await add(f"  {_synapse_line_rich()}", d(0.02))
        await add(f"  [{B3}]  ☤ hermes — artificial intelligence, genuine memory[/{B3}]", d(0.04))
        await add(f"  {_synapse_line_rich()}", d(0.02))
        await spacer(0)

        # Force layout recalc so scroll_end reaches the true bottom
        self._container.refresh(layout=True)
