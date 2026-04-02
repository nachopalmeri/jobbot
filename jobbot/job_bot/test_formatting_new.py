import sys
import unittest
from unittest.mock import MagicMock

# Mocking modules that might not be in the environment
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.constants'] = MagicMock()
sys.modules['telegram.error'] = MagicMock()
sys.modules['database'] = MagicMock()
sys.modules['job_scraper'] = MagicMock()

# Setup config mock
mock_config = MagicMock()
mock_config.CHECK_INTERVAL_HOURS = 2
sys.modules['config'] = mock_config

import scheduler

def test_html_escaping():
    print("Testing HTML escaping in format_job_message...")
    
    dirty_job = {
        "title": "Junior Developer & <Python> _Specialist_",
        "company": "Tech & Innovation <b> Ltd",
        "location": "Buenos Aires / Remote & Global",
        "source": "LinkedIn_RSS",
        "url": "https://example.com/job?id=123&ref=abc",
        "description": "This is a <i>test</i> description with *stars* and _underscores_."
    }
    
    msg = scheduler.format_job_message(dirty_job)
    print("\n--- Formatted Message ---\n")
    print(msg)
    print("\n--------------------------\n")
    
    # Check if special characters are escaped
    # "Junior Developer & <Python> _Specialist_" -> "Junior Developer &amp; &lt;Python&gt; _Specialist_"
    assert "&lt;" in msg
    assert "&gt;" in msg
    assert "&amp;" in msg
    
    # Check if tags are present (manually inserted b/i/a)
    assert "<b>" in msg
    assert "<i>" in msg
    assert "<a href=" in msg
    
    # Check if original HTML-like strings in data are escaped
    # "Tech & Innovation <b> Ltd" -> "Tech &amp; Innovation &lt;b&gt; Ltd"
    assert "Tech &amp; Innovation &lt;b&gt; Ltd" in msg
    
    # Check summary header
    header = scheduler.format_summary_header(5)
    print(f"Header: {header}")
    assert "<b>" in header
    assert "<i>" in header
    assert "5" in header

    print("✅ HTML escaping and formatting tests passed!")

if __name__ == "__main__":
    try:
        test_html_escaping()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
