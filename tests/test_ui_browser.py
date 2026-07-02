"""Real-browser E2E test of the hub UI (playwright).

Skipped automatically unless playwright + its chromium build are installed
(`pip install -e '.[e2e]' && playwright install chromium`). Launches the app
on a private port, drives an actual browser, and asserts the interactions
that broke once before: copilot toggle/ask on every page type, navbar/home
search navigation, and search-page refinement.

The copilot runs in offline extractive mode here (deterministic, no CLI).
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

playwright_sync = pytest.importorskip("playwright.sync_api")

REPO_ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    port = _free_port()
    env = {**os.environ, "ATLAS_COPILOT": "extractive", "ATLAS_DEBUG": "0"}
    proc = subprocess.Popen(
        [sys.executable, "-m", "hub.app", "--port", str(port), "--no-debug"],
        cwd=REPO_ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        for _ in range(50):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                    break
            except OSError:
                time.sleep(0.2)
        else:
            pytest.skip("hub app failed to start")
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


@pytest.fixture(scope="module")
def page(base_url):
    with playwright_sync.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            pytest.skip("chromium not installed — run: playwright install chromium")
        pg = browser.new_page()
        errors: list[str] = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.errors = errors  # type: ignore[attr-defined]
        yield pg
        browser.close()


def test_copilot_works_from_home(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    page.click("#copilot-toggle")
    page.wait_for_selector(".offcanvas.show", timeout=5000)
    page.wait_for_function(  # intro renders via async markdown chunk
        "document.querySelector('#copilot-messages').innerText.includes('Atlas copilot')",
        timeout=10000)

    page.fill("#copilot-input", "what is PSI?")
    page.press("#copilot-input", "Enter")
    page.wait_for_function(
        "document.querySelectorAll('.chat-bubble').length >= 3", timeout=15000)
    assert "Population Stability" in page.locator(".chat-assistant").last.inner_text()
    page.click(".offcanvas .btn-close")
    page.wait_for_timeout(500)


def test_navbar_search_navigates_and_renders(page, base_url):
    page.goto(base_url, wait_until="networkidle")
    nav = page.locator("input[type='search']").first
    nav.fill("NPI data")
    nav.press("Enter")
    page.wait_for_url("**/search?q=*", timeout=10000)
    page.wait_for_selector(".search-hit", timeout=10000)
    assert page.locator(".search-hit").count() > 0


def test_search_page_refine(page, base_url):
    page.goto(base_url + "/search?q=NPI", wait_until="networkidle")
    q = page.locator("input[type='search']").nth(1)
    q.fill("champion challenger")
    q.press("Enter")
    page.wait_for_function(
        "document.body.innerText.includes('Town Hall')", timeout=10000)


def test_doc_page_copilot_button(page, base_url):
    page.goto(base_url + "/doc/onboarding/welcome", wait_until="networkidle")
    page.click("text=Ask the copilot about this page")
    page.wait_for_selector(".offcanvas.show", timeout=5000)


def test_no_client_side_errors(page):
    real = [e for e in page.errors if "favicon" not in e.lower()]
    assert real == [], real
