import os
import time
import threading
import http.server
import socketserver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

os.makedirs('artifacts', exist_ok=True)

PORT = 8000
DIRECTORY = "frontend"

class DualStackServer(socketserver.TCPServer):
    allow_reuse_address = True

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    def log_message(self, format, *args):
        pass

def start_server():
    with DualStackServer(("", PORT), Handler) as httpd:
        print(f"Local dev server running on http://localhost:{PORT}")
        httpd.serve_forever()

server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()
time.sleep(2)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--window-size=1280,960')
chrome_options.add_argument('--use-fake-ui-for-media-stream')
chrome_options.add_argument('--use-fake-device-for-media-stream')
chrome_options.add_argument('--hide-scrollbars')

print("Launching automated browser...")
driver = webdriver.Chrome(options=chrome_options)

try:
    # ----------------- INITIAL AUTHENTICATION SEEDING -----------------
    print("Navigating to index.html to set domain session storage...")
    driver.get(f"http://localhost:{PORT}/index.html")
    time.sleep(2)
    
    # Inject Guest / Auth parameters to bypass all redirection filters
    driver.execute_script(
        "sessionStorage.setItem('mindhaven_guest', 'true'); "
        "sessionStorage.setItem('mindhaven_auth', 'true'); "
        "sessionStorage.setItem('mindhaven_user', 'Judge (Demo)');"
    )
    print("Session Storage successfully pre-loaded with guest state.")
    
    # ----------------- 1. LANDING PAGE -----------------
    driver.save_screenshot("artifacts/landing_page.png")
    print("Landing Page screenshot saved.")

    # ----------------- 2. DIAGNOSTIC TERMINAL (QUIZ) -----------------
    print("Navigating to Diagnostic Terminal (assess.html)...")
    driver.get(f"http://localhost:{PORT}/assess.html")
    time.sleep(3)
    driver.save_screenshot("artifacts/diagnostic_terminal_quiz.png")
    print("Diagnostic Terminal (Quiz) screenshot saved.")

    # ----------------- 3. DIAGNOSTIC TERMINAL (FACIAL SCAN) -----------------
    print("Activating Facial Scan Phase...")
    driver.execute_script("showPhase('face'); startFaceScan();")
    time.sleep(4) # Let camera simulator run and draw grid mesh
    driver.save_screenshot("artifacts/diagnostic_terminal_face.png")
    print("Diagnostic Terminal (Face Scan) screenshot saved.")

    # ----------------- 4. DIAGNOSTIC TERMINAL (VOICE SCAN) -----------------
    print("Activating Voice Scan Phase...")
    driver.execute_script("showPhase('voice'); startVoiceScan();")
    time.sleep(4) # Let waveform draw on mock microphone input
    driver.save_screenshot("artifacts/diagnostic_terminal_voice.png")
    print("Diagnostic Terminal (Voice Scan) screenshot saved.")

    # ----------------- 5. TELEMETRY INSIGHTS -----------------
    print("Navigating to Telemetry Insights (insights.html)...")
    driver.get(f"http://localhost:{PORT}/insights.html")
    time.sleep(4) # Let Three.js scene load
    
    # Open the chatbot widget
    driver.execute_script("toggleChat();")
    time.sleep(2) # Let GSAP finish
    driver.save_screenshot("artifacts/telemetry_insights.png")
    print("Telemetry Insights screenshot saved.")

    # ----------------- 6. TELEMETRY DASHBOARD (CHART.JS TRENDS) -----------------
    print("Navigating to Dashboard (dashboard.html)...")
    driver.get(f"http://localhost:{PORT}/dashboard.html")
    time.sleep(4) # Let Chart.js load and render mock records
    driver.save_screenshot("artifacts/telemetry_dashboard.png")
    print("Dashboard (Chart.js Trends) screenshot saved.")

    # ----------------- 7. PRANAYAMA STUDIO (BREATHING ORB) -----------------
    print("Navigating to Pranayama Studio (breathe.html)...")
    driver.get(f"http://localhost:{PORT}/breathe.html")
    time.sleep(3)
    
    # Start breathing cycle to expand orb
    driver.execute_script("toggleSession();")
    time.sleep(3) # Wait for 'Breathe In' expansion state
    driver.save_screenshot("artifacts/pranayama_studio.png")
    print("Pranayama Studio (Breathing Orb) screenshot saved.")

    print("\nAll Web Application UI snapshots successfully captured!")
    
except Exception as e:
    print(f"An error occurred during automation: {e}")
finally:
    print("Closing browser...")
    driver.quit()
