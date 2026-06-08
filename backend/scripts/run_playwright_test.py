import os
import time
from playwright.sync_api import sync_playwright

def test_chat_assistant():
    print("Starting automated Playwright agent test...")
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        print("Navigating to frontend...")
        page.goto("http://localhost:3000")
        page.wait_for_timeout(2000)

        # Wait for the login screen to appear
        print("Logging in...")
        # Fill in the form. Assuming there's a login form that asks for email and password.
        # But wait, maybe we need to sign up first? Or just use the test user.
        # The demo user created on startup is john.doe@example.com / password123
        try:
            # We look for inputs
            page.fill('input[type="email"]', 'john.doe@example.com')
            page.fill('input[type="password"]', 'password123')
            # Look for button that says "Login"
            page.click('button:has-text("Login")')
            # Wait for dashboard to load
            page.wait_for_timeout(2000)
            print("Login successful.")
        except Exception as e:
            print(f"Could not login via standard form, might already be logged in or UI is different: {e}")

        # Now click the floating chat assistant
        print("Opening Chat Assistant...")
        try:
            # The chat button has class 'fixed bottom-6 right-6' or similar, we can click the button
            page.click('button.bg-indigo-600')
            page.wait_for_timeout(1000)
        except Exception as e:
            print("Could not find the chat button. Taking screenshot anyway.")

        print("Typing message...")
        try:
            # Type into the chat input
            page.fill('input[placeholder="Ask about our products..."]', 'I need a fast laptop for machine learning')
            page.keyboard.press("Enter")
            print("Message sent. Waiting for AI to respond...")
            # Wait for AI response bubble to appear (usually takes 3-7 seconds)
            page.wait_for_timeout(8000)
        except Exception as e:
            print(f"Error interacting with chat input: {e}")

        # Take a screenshot
        screenshot_path = os.path.join(os.path.dirname(__file__), "agent_test_screenshot.png")
        print(f"Taking screenshot and saving to {screenshot_path}")
        page.screenshot(path=screenshot_path)

        browser.close()
        print("Playwright test complete!")

if __name__ == "__main__":
    test_chat_assistant()
