#!/usr/bin/env python3
"""
test_jobbot.py - E2E test for JobBot application

Tests basic functionality:
- Landing page loads
- Login page is accessible
- Dashboard requires authentication
- Health endpoint is accessible
"""

import pytest
from playwright.sync_api import sync_playwright
import sys

pytestmark = pytest.mark.skip(
    reason="Smoke test manual. Los E2E oficiales viven en frontend/tests/e2e."
)

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"


def test_health_endpoint():
    """Test API health endpoint."""
    print("Testing API health endpoint...")
    
    import requests
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Health endpoint OK: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"  [FAIL] Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAIL] Health endpoint error: {e}")
        return False


def test_landing_page(page):
    """Test landing page loads correctly."""
    print("Testing landing page...")
    
    try:
        page.goto(f"{BASE_URL}/", timeout=60000, wait_until="domcontentloaded")
        
        # Take screenshot
        page.screenshot(path="test_artifacts/01_landing.png", full_page=True)
        
        # Check page title
        title = page.title()
        if "JobBot" in title or "jobbot" in title.lower():
            print(f"  [OK] Page title: {title}")
        else:
            print(f"  [WARN] Page title doesn't contain 'JobBot': {title}")
        
        # Look for main elements
        headings = page.locator("h1").all()
        print(f"  [OK] Found {len(headings)} h1 heading(s)")
        
        buttons = page.locator("button, a[role='button']").all()
        print(f"  [OK] Found {len(buttons)} button(s)/links")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Error loading landing page: {e}")
        return False


def test_login_page(page):
    """Test login page is accessible."""
    print("Testing login page...")
    
    try:
        page.goto(f"{BASE_URL}/login", timeout=60000, wait_until="domcontentloaded")
        
        # Take screenshot
        page.screenshot(path="test_artifacts/02_login.png", full_page=True)
        
        # Look for Telegram login button or form
        inputs = page.locator("input").all()
        buttons = page.locator("button").all()
        
        print(f"  [OK] Found {len(inputs)} input field(s)")
        print(f"  [OK] Found {len(buttons)} button(s)")
        
        # Check for Telegram-related text
        content = page.content()
        if "telegram" in content.lower() or "Telegram" in content:
            print("  [OK] Telegram authentication reference found")
        else:
            print("  [WARN] No Telegram authentication reference found")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Error loading login page: {e}")
        return False


def test_dashboard_requires_auth(page):
    """Test that dashboard requires authentication."""
    print("Testing dashboard authentication...")
    
    try:
        page.goto(f"{BASE_URL}/dashboard", timeout=60000, wait_until="domcontentloaded")
        
        # Take screenshot
        page.screenshot(path="test_artifacts/03_dashboard_noauth.png", full_page=True)
        
        # Check current URL - should redirect to login
        current_url = page.url
        if "/login" in current_url or current_url == f"{BASE_URL}/login":
            print(f"  [OK] Dashboard redirects to login (unauthenticated)")
            return True
        elif "/dashboard" in current_url:
            print(f"  [WARN] Dashboard accessible without auth: {current_url}")
            return False
        else:
            print(f"  [INFO] Unexpected redirect: {current_url}")
            return True
    except Exception as e:
        print(f"  [FAIL] Error testing dashboard: {e}")
        return False


def test_subscription_page(page):
    """Test subscription/pricing page."""
    print("Testing subscription page...")
    
    try:
        page.goto(f"{BASE_URL}/suscripcion", timeout=60000, wait_until="domcontentloaded")
        
        # Take screenshot
        page.screenshot(path="test_artifacts/04_subscription.png", full_page=True)
        
        # Check for pricing information
        content = page.content().lower()
        has_price = any(term in content for term in ["$", "precio", "plan", "pro", "premium"])
        
        if has_price:
            print("  [OK] Pricing information found on page")
        else:
            print("  [WARN] No pricing information found")
        
        return True
    except Exception as e:
        print(f"  [FAIL] Error loading subscription page: {e}")
        return False


def main():
    print("=" * 60)
    print("JobBot E2E Test Suite")
    print("=" * 60)
    print()
    
    # Create test artifacts directory
    import os
    os.makedirs("test_artifacts", exist_ok=True)
    
    results = []
    
    # Test API health
    results.append(("API Health", test_health_endpoint()))
    print()
    
    # Test frontend with Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            results.append(("Landing Page", test_landing_page(page)))
            print()
            
            results.append(("Login Page", test_login_page(page)))
            print()
            
            results.append(("Dashboard Auth", test_dashboard_requires_auth(page)))
            print()
            
            results.append(("Subscription Page", test_subscription_page(page)))
            print()
            
        finally:
            browser.close()
    
    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status}: {name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
