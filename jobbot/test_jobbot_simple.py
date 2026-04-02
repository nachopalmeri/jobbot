#!/usr/bin/env python3
"""
test_jobbot_simple.py - Simple smoke test for JobBot

Tests:
- API health endpoint
- Legacy static landing page backup (file://)
"""

from playwright.sync_api import sync_playwright
import sys
import os

BASE_URL = "http://localhost:3000"
API_URL = "http://localhost:8000"
LANDING_HTML = "job_bot/landing/index.html"


def test_health_endpoint():
    """Test API health endpoint."""
    print("Testing API health endpoint...")
    
    import requests
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        assert response.status_code == 200, f"Health endpoint: {response.status_code}"
        data = response.json()
        print(f"  [OK] Health endpoint: {data.get('status', 'unknown')}")
    except Exception as e:
        print(f"  [FAIL] Health endpoint error: {e}")
        raise


def test_static_landing():
    """Test legacy static landing backup."""
    print("Testing legacy static landing backup...")
    
    landing_path = os.path.abspath(LANDING_HTML)
    assert os.path.exists(landing_path), f"Landing page not found: {landing_path}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Load static HTML file
            page.goto(f"file://{landing_path}", timeout=30000)
            
            # Take screenshot
            os.makedirs("test_artifacts", exist_ok=True)
            page.screenshot(path="test_artifacts/01_landing.png", full_page=True)
            
            # Check page title
            title = page.title()
            print(f"  [OK] Page title: {title}")
            
            # Look for main elements
            headings = page.locator("h1").all()
            print(f"  [OK] Found {len(headings)} h1 heading(s)")
            
            # Check for pricing section
            content = page.content().lower()
            if "precio" in content or "$" in content or "plan" in content:
                print("  [OK] Pricing/plan info found")
            else:
                print("  [WARN] No pricing info found")
        except Exception as e:
            print(f"  [FAIL] Error: {e}")
            raise
        finally:
            browser.close()


def main():
    print("=" * 60)
    print("JobBot Simple Smoke Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test API
    results.append(("API Health", test_health_endpoint()))
    print()
    
    # Test static landing page
    results.append(("Static Landing Page", test_static_landing()))
    print()
    
    # Summary
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
