import sys

import pytest
from conftest import make_fake_st


class FakeClient:
    def __init__(self, url, token, ssl_verify=True):
        self.url = url
        self.token = token
        self.ssl_verify = ssl_verify
        self.client = "fake-client"


@pytest.fixture(autouse=True)
def reimport_main(monkeypatch):
    if "gitlab_compliance_checker.ui.main" in sys.modules:
        del sys.modules["gitlab_compliance_checker.ui.main"]

    monkeypatch.setenv("GITLAB_URL", "https://gitlab.com")
    monkeypatch.setenv("GITLAB_TOKEN", "token")
    sys.modules["streamlit"] = make_fake_st([], "Check Project Compliance")
    sys.modules["dotenv"] = type("Dotenv", (), {"load_dotenv": lambda: None})

    from gitlab_compliance_checker.ui import main

    yield main

    for m in ["gitlab_compliance_checker.ui.main", "streamlit", "dotenv"]:
        if m in sys.modules:
            del sys.modules[m]


def test_main_no_token(monkeypatch, reimport_main):
    main_mod = reimport_main
    monkeypatch.setenv("GITLAB_TOKEN", "")
    fake_st = make_fake_st([], "Check Project Compliance")
    main_mod.st = fake_st
    monkeypatch.setattr(main_mod, "GitLabClient", FakeClient)

    with pytest.raises(SystemExit):
        main_mod.main()

    assert "GITLAB_TOKEN is not set" in fake_st.messages["warning"][0]


def test_main_client_init_error(monkeypatch, reimport_main):
    main_mod = reimport_main
    fake_st = make_fake_st([], "Check Project Compliance")
    main_mod.st = fake_st

    class BadClient:
        def __init__(self, url, token, ssl_verify=True):
            raise Exception("boom")

    monkeypatch.setattr(main_mod, "GitLabClient", BadClient)

    with pytest.raises(SystemExit):
        main_mod.main()

    assert "Critical Error initializing GitLab client" in fake_st.messages["error"][0]


def test_main_mode_routing_check_project(monkeypatch, reimport_main):
    main_mod = reimport_main
    fake_st = make_fake_st([], "Check Project Compliance")
    main_mod.st = fake_st
    monkeypatch.setattr(main_mod, "GitLabClient", FakeClient)

    called = {}

    def fake_render_compliance_mode(client_obj):
        called["compliance"] = client_obj

    monkeypatch.setattr(main_mod, "render_compliance_mode", fake_render_compliance_mode)

    main_mod.main()

    assert called["compliance"].client == "fake-client"


def test_app_run_as_script_calls_main(monkeypatch):
    """Ensure app.py runs without errors as __main__."""
    import types as _types

    monkeypatch.setenv("GITLAB_URL", "https://gitlab.com")
    monkeypatch.setenv("GITLAB_TOKEN", "token")
    fake_st = make_fake_st([], "Check Project Compliance")
    monkeypatch.setitem(sys.modules, "streamlit", fake_st)
    monkeypatch.setitem(sys.modules, "dotenv", type("Dotenv", (), {"load_dotenv": lambda: None}))
    monkeypatch.setitem(
        sys.modules,
        "gitlab_compliance_checker.ui.compliance",
        _types.SimpleNamespace(render_compliance_mode=lambda c: None),
    )

    if "app" in sys.modules:
        del sys.modules["app"]
    if "gitlab_compliance_checker.ui.main" in sys.modules:
        del sys.modules["gitlab_compliance_checker.ui.main"]

    import runpy

    runpy.run_path("app.py", run_name="__main__")
