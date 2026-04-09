"""
End-to-End Tests using Playwright for JobBot Dashboard
Critical user flows: Login → Dashboard → Buscar Jobs → Aplicar
"""

import re
from playwright.sync_api import Page, expect, BrowserContext

# Base URL for testing
BASE_URL = "http://localhost:3000"  # Frontend development server
API_URL = "http://localhost:8000"  # API server


def test_login_flow(page: Page):
    """
    Test: Login → Dashboard
    Critical path: User must be able to log in and reach dashboard
    """
    # Navigate to login page
    page.goto(f"{BASE_URL}/login")

    # Verify login page loaded
    expect(page).to_have_title(re.compile("Login|JobBot"))

    # Fill in credentials
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='password']", "testpassword123")

    # Click login button
    page.click("button[type='submit']")

    # Wait for navigation to dashboard
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)

    # Verify dashboard loaded
    expect(page).to_have_url(f"{BASE_URL}/dashboard")
    expect(page.locator("text=Dashboard")).to_be_visible()

    # Verify user info is displayed
    expect(page.locator("text=test@example.com")).to_be_visible()


def test_login_with_invalid_credentials(page: Page):
    """Test login with invalid credentials shows error."""
    page.goto(f"{BASE_URL}/login")

    # Fill in wrong credentials
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='password']", "wrongpassword")

    page.click("button[type='submit']")

    # Verify error message appears
    expect(page.locator("text=Invalid")).to_be_visible()

    # Verify still on login page
    expect(page).to_have_url(re.compile("/login"))


def test_registration_flow(page: Page):
    """
    Test: Registro completo
    Critical path: New user must be able to register
    """
    page.goto(f"{BASE_URL}/register")

    # Verify registration page loaded
    expect(page).to_have_title(re.compile("Register|Sign Up|JobBot"))

    # Fill in registration form
    page.fill("input[name='name']", "Test User")
    page.fill("input[name='email']", "newuser@example.com")
    page.fill("input[name='password']", "SecurePass123!")
    page.fill("input[name='confirmPassword']", "SecurePass123!")

    # Submit form
    page.click("button[type='submit']")

    # Should redirect to dashboard or show success
    try:
        page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)
        expect(page).to_have_url(f"{BASE_URL}/dashboard")
    except:
        # If not redirected, should show success message
        expect(page.locator("text=success")).to_be_visible()


def test_dashboard_job_search_flow(page: Page, context: BrowserContext):
    """
    Test: Login → Dashboard → Buscar Jobs
    Critical path: User must be able to search for jobs
    """
    # First, log in via API and set up auth state
    # This simulates being logged in
    page.goto(f"{BASE_URL}/dashboard")

    # If redirected to login, need to authenticate first
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard")

    # Now on dashboard, click on job search
    page.click("text=Buscar Trabajos")

    # Wait for search page
    page.wait_for_url(re.compile("/jobs|/search"))

    # Fill in search query
    page.fill("input[name='query']", "Python Developer")

    # Click search button
    page.click("button:has-text('Buscar')")

    # Wait for results
    page.wait_for_selector("[data-testid='job-card'], .job-card", timeout=10000)

    # Verify results are displayed
    job_cards = page.locator("[data-testid='job-card'], .job-card")
    expect(job_cards.first).to_be_visible()


def test_job_application_flow(page: Page):
    """
    Test: Dashboard → Buscar Jobs → Aplicar
    Critical path: User must be able to apply to a job
    """
    # Navigate to jobs page
    page.goto(f"{BASE_URL}/jobs")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/jobs")

    # Wait for job cards to load
    page.wait_for_selector("[data-testid='job-card'], .job-card", timeout=10000)

    # Click on first job card
    first_job = page.locator("[data-testid='job-card'], .job-card").first
    first_job.click()

    # Wait for job detail modal/page
    page.wait_for_selector("[data-testid='job-detail'], .job-detail", timeout=5000)

    # Click apply button
    page.click("button:has-text('Aplicar')")

    # Verify application modal/form appears
    expect(page.locator("text=Aplicación")).to_be_visible()

    # Fill in application notes
    page.fill("textarea[name='notes']", "Me interesa esta posición")

    # Submit application
    page.click("button:has-text('Enviar')")

    # Verify success message
    expect(page.locator("text=Aplicación enviada")).to_be_visible()


def test_payment_flow_stripe_test_mode(page: Page):
    """
    Test: Payment flow with Stripe test mode
    Critical path: User must be able to upgrade subscription
    """
    # Navigate to subscriptions page
    page.goto(f"{BASE_URL}/subscriptions")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/subscriptions")

    # Verify subscription page loaded
    expect(page.locator("text=Suscripción")).to_be_visible()

    # Click upgrade to pro
    page.click("button:has-text('Pro')")

    # Wait for Stripe checkout redirect
    page.wait_for_url(re.compile("checkout.stripe.com"), timeout=10000)

    # Fill in Stripe test card details
    # Note: In test mode, use test card numbers
    page.fill("input[name='cardNumber']", "4242 4242 4242 4242")
    page.fill("input[name='cardExpiry']", "12/25")
    page.fill("input[name='cardCvc']", "123")
    page.fill("input[name='billingName']", "Test User")

    # Submit payment
    page.click("button[type='submit']")

    # Wait for redirect back to success page
    page.wait_for_url(f"{BASE_URL}/success", timeout=30000)

    # Verify success
    expect(page.locator("text=¡Gracias!")).to_be_visible()


def test_logout_flow(page: Page):
    """Test logout functionality."""
    # Navigate to dashboard (assumes logged in)
    page.goto(f"{BASE_URL}/dashboard")

    # Click logout button/link
    page.click("text=Logout, text=Cerrar sesión, [data-testid='logout']")

    # Should redirect to login page
    page.wait_for_url(f"{BASE_URL}/login")

    # Verify on login page
    expect(page).to_have_url(f"{BASE_URL}/login")

    # Try to access dashboard again - should redirect to login
    page.goto(f"{BASE_URL}/dashboard")
    expect(page).to_have_url(f"{BASE_URL}/login")


def test_user_preferences_update(page: Page):
    """Test updating user preferences."""
    # Navigate to settings/preferences
    page.goto(f"{BASE_URL}/settings")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/settings")

    # Update experience level
    page.select_option("select[name='experience_level']", "senior")

    # Update role type
    page.fill("input[name='role_type']", "Backend Developer")

    # Update technologies
    page.fill("input[name='technologies']", "Python, FastAPI, PostgreSQL")

    # Save changes
    page.click("button:has-text('Guardar')")

    # Verify success message
    expect(page.locator("text=Preferencias guardadas")).to_be_visible()


def test_cv_upload_flow(page: Page):
    """Test CV upload flow."""
    # Navigate to CV page
    page.goto(f"{BASE_URL}/cv")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/cv")

    # Upload CV file
    with page.expect_filechooser() as fc_info:
        page.click("button:has-text('Subir CV')")
    file_chooser = fc_info.value
    file_chooser.set_files("test_cv.pdf")

    # Wait for upload to complete
    page.wait_for_selector("text=CV subido", timeout=10000)

    # Verify success
    expect(page.locator("text=CV subido")).to_be_visible()


def test_application_tracking_dashboard(page: Page):
    """Test application tracking dashboard."""
    # Navigate to applications page
    page.goto(f"{BASE_URL}/applications")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/applications")

    # Verify page loaded
    expect(page.locator("text=Mis Aplicaciones")).to_be_visible()

    # Verify applications list is displayed
    # (Might be empty or have items)
    expect(page.locator("[data-testid='applications-list']")).to_be_visible()


def test_responsive_mobile_layout(page: Page):
    """Test responsive design on mobile viewport."""
    # Set mobile viewport
    page.set_viewport_size({"width": 375, "height": 667})

    # Navigate to login
    page.goto(f"{BASE_URL}/login")

    # Verify mobile menu is present
    expect(page.locator("[data-testid='mobile-menu'], .mobile-menu")).to_be_visible()

    # Verify form elements are accessible
    expect(page.locator("input[name='email']")).to_be_visible()
    expect(page.locator("input[name='password']")).to_be_visible()


def test_accessibility_keyboard_navigation(page: Page):
    """Test keyboard navigation accessibility."""
    page.goto(f"{BASE_URL}/login")

    # Tab through form fields
    page.keyboard.press("Tab")
    expect(page.locator("input[name='email']")).to_be_focused()

    page.keyboard.press("Tab")
    expect(page.locator("input[name='password']")).to_be_focused()

    page.keyboard.press("Tab")
    expect(page.locator("button[type='submit']")).to_be_focused()

    # Fill form using keyboard only
    page.fill("input[name='email']", "test@example.com")
    page.fill("input[name='password']", "testpassword123")

    # Submit with Enter
    page.keyboard.press("Enter")

    # Should navigate to dashboard
    page.wait_for_url(f"{BASE_URL}/dashboard", timeout=5000)


def test_error_boundary_catch(page: Page):
    """Test that error boundaries catch React errors."""
    page.goto(f"{BASE_URL}/dashboard")

    # Simulate an error (this depends on the app having error boundaries)
    page.evaluate("() => { window.simulateError = true; }")

    # Navigate to a page that might throw
    page.goto(f"{BASE_URL}/error-test")

    # Should show error boundary UI instead of blank page
    expect(page.locator("text=Algo salió mal")).to_be_visible()

    # Should have reload button
    expect(page.locator("button:has-text('Recargar')")).to_be_visible()


def test_dark_mode_toggle(page: Page):
    """Test dark mode toggle functionality."""
    page.goto(f"{BASE_URL}/dashboard")

    # If redirected to login, authenticate
    if "/login" in page.url:
        page.fill("input[name='email']", "test@example.com")
        page.fill("input[name='password']", "testpassword123")
        page.click("button[type='submit']")
        page.wait_for_url(f"{BASE_URL}/dashboard")

    # Find and click dark mode toggle
    page.click("[data-testid='dark-mode-toggle'], button[aria-label*='dark']")

    # Verify dark class is applied to html or body
    html_class = page.evaluate("() => document.documentElement.className")
    assert "dark" in html_class or page.locator(".dark").count() > 0
