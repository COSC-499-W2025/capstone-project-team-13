import builtins
from dataclasses import dataclass, field
from datetime import datetime, timezone
import types
import pytest
import src.UserPrompts.config_integration as mod


# -------------------------
# Fakes / helpers
# -------------------------

@dataclass
class FakeConfig:
    # Consent
    basic_consent_granted: bool = False
    basic_consent_timestamp: datetime | None = None

    ai_consent_granted: bool = False
    ai_consent_timestamp: datetime | None = None
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o-mini"
    ai_enabled: bool = False

    # Privacy
    anonymous_mode: bool = False
    store_file_contents: bool = True
    store_contributor_names: bool = True
    store_file_paths: bool = True

    excluded_folders: list[str] = field(default_factory=list)
    excluded_file_types: list[str] = field(default_factory=list)
    max_file_size_scan: int = 10_000_000  # 10MB

    # Scanning prefs
    auto_detect_project_type: bool = True
    scan_nested_folders: bool = True
    max_scan_depth: int = 5
    skip_hidden_files: bool = True

    # Analysis features
    enable_keyword_extraction: bool = True
    enable_language_detection: bool = True
    enable_framework_detection: bool = True
    enable_collaboration_analysis: bool = True
    enable_duplicate_detection: bool = True

    # UI / Output prefs
    theme: str = "light"
    language: str = "en"
    show_progress_indicators: bool = True
    default_export_format: str = "json"
    summary_detail_level: str = "standard"
    resume_max_projects: int = 10

    # AI knobs
    ai_cache_enabled: bool = True
    max_tokens: int = 1024
    temperature: float = 0.2


class FakeConfigManager:
    def __init__(self, cfg: FakeConfig):
        self.cfg = cfg
        self.updated = []          # list[dict]
        self.revoked_basic = 0
        self.granted_basic = 0
        self.revoked_ai = 0
        self.granted_ai = 0
        self.added_folders = []
        self.added_types = []

    def get_or_create_config(self):
        return self.cfg

    def update_config(self, patch: dict):
        self.updated.append(patch)
        for k, v in patch.items():
            setattr(self.cfg, k, v)

    def grant_basic_consent(self):
        self.granted_basic += 1
        self.cfg.basic_consent_granted = True
        self.cfg.basic_consent_timestamp = datetime.now(timezone.utc)

    def revoke_basic_consent(self):
        self.revoked_basic += 1
        self.cfg.basic_consent_granted = False
        self.cfg.basic_consent_timestamp = None

    def grant_ai_consent(self):
        self.granted_ai += 1
        self.cfg.ai_consent_granted = True
        self.cfg.ai_enabled = True
        self.cfg.ai_consent_timestamp = datetime.now(timezone.utc)

    def revoke_ai_consent(self):
        self.revoked_ai += 1
        self.cfg.ai_consent_granted = False
        self.cfg.ai_enabled = False
        self.cfg.ai_consent_timestamp = None

    def add_excluded_folder(self, folder: str):
        self.added_folders.append(folder)
        self.cfg.excluded_folders.append(folder)

    def add_excluded_file_type(self, ext: str):
        self.added_types.append(ext)
        self.cfg.excluded_file_types.append(ext)


def feed_inputs(monkeypatch, answers: list[str]):
    """
    Patch builtins.input to return items from answers in order.
    Raises AssertionError if code asks for more inputs than provided.
    """
    it = iter(answers)

    def fake_input(prompt=""):
        try:
            return next(it)
        except StopIteration:
            raise AssertionError(f"Unexpected extra input prompt: {prompt!r}")

    monkeypatch.setattr(builtins, "input", fake_input)


@pytest.fixture
def fake_env(monkeypatch):
    """
    Replace module-level config_manager with a fake.
    """
    cfg = FakeConfig()
    mgr = FakeConfigManager(cfg)
    monkeypatch.setattr(mod, "config_manager", mgr)
    return cfg, mgr


# -------------------------
# format_local_time tests
# -------------------------

def test_format_local_time_none():
    assert mod.format_local_time(None) == "Unknown"


def test_format_local_time_naive_assumed_utc():
    # Naive: assume UTC
    ts = datetime(2025, 11, 12, 4, 30, 0)  # naive
    out = mod.format_local_time(ts)
    # Should be a string with the same moment rendered locally.
    # We can't assert the exact local time across environments, but it should parse and be stable format.
    assert len(out) == 19
    assert out.count("-") == 2
    assert out.count(":") == 2


def test_format_local_time_aware_utc():
    ts = datetime(2025, 11, 12, 4, 30, 0, tzinfo=timezone.utc)
    out = mod.format_local_time(ts)
    assert len(out) == 19


# -------------------------
# Basic consent tests
# -------------------------

def test_basic_consent_already_granted_confirm_yes(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    cfg.basic_consent_granted = True
    cfg.basic_consent_timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)

    feed_inputs(monkeypatch, ["y"])  # any other input counts as consent
    assert mod.request_and_store_basic_consent() is True
    assert mgr.revoked_basic == 0

    out = capsys.readouterr().out
    assert "previously granted" in out.lower()


def test_basic_consent_already_granted_confirm_no(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    cfg.basic_consent_granted = True
    cfg.basic_consent_timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)

    feed_inputs(monkeypatch, ["no"])
    assert mod.request_and_store_basic_consent() is False
    assert mgr.revoked_basic == 1

    out = capsys.readouterr().out
    assert "revoked" in out.lower()


def test_basic_consent_new_allow(monkeypatch, fake_env):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["allow"])
    assert mod.request_and_store_basic_consent() is True
    assert mgr.granted_basic == 1
    assert cfg.basic_consent_granted is True


def test_basic_consent_new_deny(monkeypatch, fake_env):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["deny"])
    assert mod.request_and_store_basic_consent() is False
    assert mgr.revoked_basic == 1
    assert cfg.basic_consent_granted is False


def test_basic_consent_invalid_then_allow(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["maybe", "allow"])
    assert mod.request_and_store_basic_consent() is True
    out = capsys.readouterr().out.lower()
    assert "invalid response" in out
    assert mgr.granted_basic == 1


# -------------------------
# AI consent tests
# -------------------------

def test_ai_consent_already_granted_confirm_yes(monkeypatch, fake_env):
    cfg, mgr = fake_env
    cfg.ai_consent_granted = True
    cfg.ai_enabled = True
    cfg.ai_consent_timestamp = datetime(2025, 1, 2, tzinfo=timezone.utc)
    cfg.ai_provider = "openai"
    cfg.ai_model = "gpt-x"

    feed_inputs(monkeypatch, ["y"])
    assert mod.request_and_store_ai_consent() is True
    assert mgr.revoked_ai == 0


def test_ai_consent_already_granted_confirm_no_only(monkeypatch, fake_env):
    """
    NOTE: Your code checks `if response == 'no':` but prompt says 'no' or 'n'.
    This test verifies current behavior: typing 'n' DOES NOT revoke.
    """
    cfg, mgr = fake_env
    cfg.ai_consent_granted = True
    cfg.ai_enabled = True
    cfg.ai_consent_timestamp = datetime(2025, 1, 2, tzinfo=timezone.utc)

    feed_inputs(monkeypatch, ["n"])  # should probably revoke, but currently won't
    assert mod.request_and_store_ai_consent() is True
    assert mgr.revoked_ai == 0


def test_ai_consent_already_granted_confirm_no_revokes(monkeypatch, fake_env):
    cfg, mgr = fake_env
    cfg.ai_consent_granted = True
    cfg.ai_enabled = True
    cfg.ai_consent_timestamp = datetime(2025, 1, 2, tzinfo=timezone.utc)

    feed_inputs(monkeypatch, ["no"])
    assert mod.request_and_store_ai_consent() is False
    assert mgr.revoked_ai == 1


def test_ai_consent_new_yes(monkeypatch, fake_env):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["yes"])
    assert mod.request_and_store_ai_consent() is True
    assert mgr.granted_ai == 1
    assert cfg.ai_consent_granted is True
    assert cfg.ai_enabled is True


def test_ai_consent_new_no(monkeypatch, fake_env):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["no"])
    assert mod.request_and_store_ai_consent() is False
    assert mgr.revoked_ai == 1
    assert cfg.ai_consent_granted is False


def test_ai_consent_invalid_then_yes(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["maybe", "y"])
    assert mod.request_and_store_ai_consent() is True
    out = capsys.readouterr().out.lower()
    assert "invalid response" in out
    assert mgr.granted_ai == 1


# -------------------------
# configure_privacy_settings tests
# -------------------------

def test_configure_privacy_settings_toggle_and_add(monkeypatch, fake_env):
    cfg, mgr = fake_env
    # Flow:
    # anonymous: yes
    # store file contents: no
    # store contributor names: yes
    # store full paths: skip
    # add folders? yes -> add "C:\\temp" then done
    # add file types? yes -> add ".log" then done
    # change max file size? yes -> 2.5
    feed_inputs(monkeypatch, [
        "yes",
        "no",
        "yes",
        "skip",
        "yes", r"C:\temp", "done",
        "yes", ".log", "done",
        "yes", "2.5",
    ])

    mod.configure_privacy_settings()

    assert cfg.anonymous_mode is True
    assert cfg.store_file_contents is False
    assert cfg.store_contributor_names is True
    # store_file_paths unchanged because "skip"
    assert cfg.store_file_paths is True

    assert r"C:\temp" in cfg.excluded_folders
    assert ".log" in cfg.excluded_file_types
    assert cfg.max_file_size_scan == 2_500_000


def test_configure_privacy_settings_invalid_size_keeps(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    old = cfg.max_file_size_scan
    feed_inputs(monkeypatch, [
        "skip",       # anonymous
        "skip",       # store file contents
        "skip",       # store contributor
        "skip",       # store full paths
        "no",         # add folders
        "no",         # add file types
        "yes", "nope" # change size -> invalid
    ])
    mod.configure_privacy_settings()
    assert cfg.max_file_size_scan == old
    out = capsys.readouterr().out.lower()
    assert "invalid" in out


# -------------------------
# configure_analysis_preferences tests
# -------------------------

def test_configure_analysis_enable_all(monkeypatch, fake_env):
    cfg, mgr = fake_env
    # Option 1
    feed_inputs(monkeypatch, ["1"])
    mod.configure_analysis_preferences()
    assert cfg.enable_keyword_extraction is True
    assert cfg.enable_duplicate_detection is True


def test_configure_analysis_disable_all(monkeypatch, fake_env):
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["2"])
    mod.configure_analysis_preferences()
    assert cfg.enable_keyword_extraction is False
    assert cfg.enable_duplicate_detection is False


def test_configure_analysis_individual(monkeypatch, fake_env):
    cfg, mgr = fake_env
    # Option 3 then per feature responses
    # keyword: no, language: yes, framework: skip, collab: no, duplicate: yes
    feed_inputs(monkeypatch, ["3", "no", "yes", "skip", "n", "y"])
    mod.configure_analysis_preferences()
    assert cfg.enable_keyword_extraction is False
    assert cfg.enable_language_detection is True
    # framework unchanged
    assert cfg.enable_framework_detection is True
    assert cfg.enable_collaboration_analysis is False
    assert cfg.enable_duplicate_detection is True


def test_configure_analysis_keep_current(monkeypatch, fake_env):
    cfg, mgr = fake_env
    # Option 4 does nothing
    cfg.enable_keyword_extraction = True
    feed_inputs(monkeypatch, ["4"])
    mod.configure_analysis_preferences()
    assert cfg.enable_keyword_extraction is True


# -------------------------
# show_current_configuration tests
# -------------------------

def test_show_current_configuration_prints(monkeypatch, fake_env, capsys):
    cfg, mgr = fake_env
    cfg.basic_consent_granted = True
    cfg.basic_consent_timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
    cfg.ai_consent_granted = True
    cfg.ai_enabled = True
    cfg.ai_consent_timestamp = datetime(2025, 1, 2, tzinfo=timezone.utc)
    cfg.excluded_folders = ["A", "B", "C", "D"]

    mod.show_current_configuration()
    out = capsys.readouterr().out
    assert "CURRENT CONFIGURATION" in out
    assert "CONSENT STATUS" in out
    assert "PRIVACY SETTINGS" in out
    assert "... and 1 more" in out  # because 4 folders prints 3 + summary


# -------------------------
# quick_setup_wizard tests
# -------------------------

def test_quick_setup_wizard_cancel_if_no_basic_consent(monkeypatch, fake_env):
    # Step1 denies => returns False
    feed_inputs(monkeypatch, ["deny"])
    assert mod.quick_setup_wizard() is False


def test_quick_setup_wizard_happy_path(monkeypatch, fake_env):
    """
    Flow:
      - basic consent: allow
      - ai config now? no
      - privacy choice: 2 (max privacy)
      - enable all features? yes
      - press enter
    """
    cfg, mgr = fake_env
    feed_inputs(monkeypatch, ["allow", "no", "2", "yes", ""])  # final Enter
    assert mod.quick_setup_wizard() is True
    assert cfg.basic_consent_granted is True
    assert cfg.anonymous_mode is True
    assert cfg.store_file_contents is False
    assert cfg.store_contributor_names is False
    assert cfg.enable_keyword_extraction is True


# -------------------------
# Convenience getters tests
# -------------------------

def test_has_basic_consent(fake_env):
    cfg, mgr = fake_env
    cfg.basic_consent_granted = True
    assert mod.has_basic_consent() is True
    cfg.basic_consent_granted = False
    assert mod.has_basic_consent() is False


def test_has_ai_consent(fake_env):
    cfg, mgr = fake_env
    cfg.ai_consent_granted = True
    cfg.ai_enabled = True
    assert mod.has_ai_consent() is True
    cfg.ai_enabled = False
    assert mod.has_ai_consent() is False


def test_is_anonymous_mode(fake_env):
    cfg, mgr = fake_env
    cfg.anonymous_mode = True
    assert mod.is_anonymous_mode() is True


