"""Tests for the profiles collector and panel."""

import pytest
from hermes_hud.collectors.profiles import collect_profiles
from hermes_hud.models import ProfileInfo, ProfilesState


class TestProfilesCollector:
    """Test collect_profiles against fake hermes home."""

    def test_finds_default_and_custom_profiles(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        assert profiles.total == 2
        names = [p.name for p in profiles.profiles]
        assert "default" in names
        assert "social" in names

    def test_default_profile_is_marked(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        default = [p for p in profiles.profiles if p.name == "default"][0]
        assert default.is_default is True

    def test_default_profile_reads_config(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        default = [p for p in profiles.profiles if p.name == "default"][0]
        assert default.model == "claude-sonnet-4-20250514"
        assert default.provider == "anthropic"

    def test_custom_profile_reads_config(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert social.model == "gemma-4-26b"
        assert social.provider == "custom"
        assert social.base_url == "http://localhost:8081/v1"
        assert social.port == 8081
        assert social.context_length == 32768
        assert social.skin == "ares"

    def test_custom_profile_reads_soul(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert "social media assistant" in social.soul_summary.lower()

    def test_custom_profile_session_stats(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert social.session_count == 1
        assert social.message_count == 8
        assert social.tool_call_count == 2

    def test_custom_profile_memory_stats(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert social.memory_entries == 2
        assert social.memory_chars > 0
        assert social.user_entries == 1

    def test_custom_profile_skills(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert social.skill_count == 1

    def test_custom_profile_toolsets(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert "web" in social.toolsets
        assert "terminal" in social.toolsets

    def test_custom_profile_api_keys(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert "TELEGRAM_BOT_TOKEN" in social.api_keys

    def test_custom_profile_compression(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert social.compression_enabled is True
        assert social.compression_model == "gemma-4-26b"

    def test_is_local_detection(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        default = [p for p in profiles.profiles if p.name == "default"][0]
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert default.is_local is False
        assert social.is_local is True

    def test_profiles_state_properties(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        assert len(profiles.local_profiles()) == 1
        assert len(profiles.api_profiles()) == 1

    def test_default_profile_session_stats(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        default = [p for p in profiles.profiles if p.name == "default"][0]
        assert default.session_count == 3
        assert default.message_count == 45  # 10 + 15 + 20

    def test_capacity_pct_properties(self, fake_hermes_home):
        profiles = collect_profiles(fake_hermes_home)
        social = [p for p in profiles.profiles if p.name == "social"][0]
        assert 0 <= social.memory_capacity_pct <= 100
        assert 0 <= social.user_capacity_pct <= 100

    def test_empty_profiles_dir(self, tmp_path):
        """No profiles subdir — should just return default."""
        hermes = tmp_path / ".hermes"
        hermes.mkdir()
        profiles = collect_profiles(str(hermes))
        assert profiles.total == 1
        assert profiles.profiles[0].name == "default"
