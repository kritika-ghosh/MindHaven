import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Create output folder
os.makedirs('artifacts', exist_ok=True)

html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MindHaven System Architecture</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <style>
        body {
            margin: 0;
            padding: 0;
            background-color: #0c0d14;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 1200px;
            height: 700px;
            overflow: hidden;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        svg {
            background-color: #0c0d14;
        }
        .node-bg {
            fill: #11121d;
            stroke-width: 1.5;
        }
        .header-text {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 800;
            font-size: 13.5px;
            letter-spacing: 1px;
            fill: #ffffff;
        }
        .subheader-text {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 600;
            font-size: 10px;
            fill: #787a93;
            letter-spacing: 0.5px;
        }
        .item-text {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 500;
            font-size: 11px;
            fill: #b5b7cd;
        }
        .mono-text {
            font-family: 'Share Tech Mono', monospace;
            font-size: 10px;
            fill: #00f2fe;
        }
        .connector-line {
            fill: none;
            stroke-width: 2;
            stroke-dasharray: 4 3;
            animation: dash 30s linear infinite;
        }
        .solid-connector {
            fill: none;
            stroke-width: 2;
        }
        .label-text {
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-weight: 700;
            font-size: 10px;
            fill: #8588a5;
        }
        .badge {
            font-family: 'Share Tech Mono', monospace;
            font-size: 9px;
            font-weight: bold;
            fill: #ffffff;
        }
    </style>
</head>
<body>
    <svg width="1200" height="700" viewBox="0 0 1200 700" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <!-- Grid Pattern -->
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1f2235" stroke-width="0.8" stroke-opacity="0.4" />
            </pattern>

            <!-- Glow Filters -->
            <filter id="glow-purple" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                </feMerge>
            </filter>
            
            <!-- Gradients -->
            <linearGradient id="grad-purple" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#8455ef" />
                <stop offset="100%" stop-color="#ff007f" />
            </linearGradient>
            <linearGradient id="grad-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#00f2fe" />
                <stop offset="100%" stop-color="#4facfe" />
            </linearGradient>
            <linearGradient id="grad-orange" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#f9d423" />
                <stop offset="100%" stop-color="#ff4e50" />
            </linearGradient>
            <linearGradient id="grad-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#10b981" />
                <stop offset="100%" stop-color="#059669" />
            </linearGradient>

            <!-- Arrow Markers -->
            <marker id="arrow-purple" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#8455ef" />
            </marker>
            <marker id="arrow-cyan" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#00f2fe" />
            </marker>
            <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#ff4e50" />
            </marker>
            <marker id="arrow-emerald" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981" />
            </marker>
            <marker id="arrow-grey" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 2 L 6 5 L 0 8 z" fill="#3f4257" />
            </marker>
        </defs>

        <!-- Background grid -->
        <rect width="1200" height="700" fill="url(#grid)" />

        <!-- TITLE HEADER -->
        <text x="50" y="55" font-family="'Plus Jakarta Sans', sans-serif" font-weight="900" font-size="20px" fill="#ffffff" letter-spacing="2px">MINDHAVEN SYSTEM ARCHITECTURE</text>
        <text x="50" y="78" font-family="'Plus Jakarta Sans', sans-serif" font-weight="700" font-size="11px" fill="#8455ef" letter-spacing="1px">END-TO-END TELEMETRY FLOW & LLM COGNITIVE THERAPY WIDGET</text>
        <line x1="50" y1="92" x2="1150" y2="92" stroke="#1f2235" stroke-width="1.5" />

        <!-- ==================== NODE 1: EDGE CLIENT (LEFT) ==================== -->
        <g transform="translate(50, 130)">
            <!-- Outer Glow / Node Border -->
            <rect width="300" height="480" rx="16" ry="16" class="node-bg" stroke="url(#grad-purple)" filter="url(#glow-purple)" stroke-opacity="0.9" />
            
            <!-- Header -->
            <rect width="300" height="42" rx="16" ry="16" fill="#181424" />
            <rect y="32" width="300" height="10" fill="#181424" />
            <circle cx="20" cy="21" r="5" fill="#ff007f" />
            <text x="35" y="26" class="header-text">EDGE FEATURE EXTRACTION</text>
            <text x="35" y="37" class="subheader-text">CLIENT WEBAPP BROWSER CORE</text>
            <line x1="0" y1="42" x2="300" y2="42" stroke="#2a223f" stroke-width="1.5" />

            <!-- Content -->
            <!-- Section A: Facial Tracking -->
            <rect x="15" y="60" width="270" height="120" rx="8" ry="8" fill="#151624" stroke="#25203a" stroke-width="1" />
            <text x="30" y="82" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#da77f2">FACIAL EXPRESSION TRACKING</text>
            <text x="30" y="105" class="item-text">• Real-time Eye & Mouth aspect ratios</text>
            <text x="40" y="125" class="mono-text">EAR = (p2-p6 + p3-p5) / (2 * (p1-p4))</text>
            <text x="40" y="142" class="mono-text">MAR = (p13-p19) / (p11-p17)</text>
            <text x="30" y="162" class="item-text">• Landmark vector processing (Mediapipe)</text>

            <!-- Section B: Audio Capture -->
            <rect x="15" y="195" width="270" height="110" rx="8" ry="8" fill="#151624" stroke="#25203a" stroke-width="1" />
            <text x="30" y="217" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#ff4e50">WEB AUDIO CAPTURE & SENTIMENT</text>
            <text x="30" y="240" class="item-text">• Web Audio API audio-recorder node</text>
            <text x="30" y="258" class="item-text">• VADER Tone Sentiment extraction</text>
            <text x="40" y="275" class="mono-text">Compound Score in [-1.0, 1.0]</text>
            <text x="30" y="292" class="item-text">• Speech-to-Text lexical transcript</text>

            <!-- Section C: HUD Chat Interface -->
            <rect x="15" y="320" width="270" height="140" rx="8" ry="8" fill="#151624" stroke="#25203a" stroke-width="1" />
            <text x="30" y="342" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#8455ef">HUD DIAGNOSTICS & CHAT WIDGET</text>
            <text x="30" y="365" class="item-text">• 5-Question Psychometric Survey UI</text>
            <text x="30" y="382" class="item-text">• Glassmorphic Floating CBT Chatbot</text>
            <text x="30" y="400" class="item-text">• Interactive Vitality Orb (Three.js WebGL)</text>
            <text x="30" y="418" class="item-text">• Real-time Chart.js telemetry rendering</text>
            <text x="30" y="442" font-family="'Share Tech Mono', monospace" font-size="9.5px" fill="#8455ef">STATUS: CONNECTED & CAPTURING</text>
        </g>

        <!-- ==================== NODE 2: CATBOOST REGRESSOR (MIDDLE TOP) ==================== -->
        <g transform="translate(450, 130)">
            <rect width="280" height="210" rx="16" ry="16" class="node-bg" stroke="url(#grad-orange)" stroke-width="2" />
            
            <!-- Header -->
            <rect width="280" height="42" rx="16" ry="16" fill="#241f17" />
            <rect y="32" width="280" height="10" fill="#241f17" />
            <circle cx="20" cy="21" r="5" fill="#f9d423" />
            <text x="35" y="26" class="header-text">CATBOOST SCORING ENGINE</text>
            <text x="35" y="37" class="subheader-text">BURNOUT REGRESSION MODEL</text>
            <line x1="0" y1="42" x2="280" y2="42" stroke="#3c3120" stroke-width="1.5" />

            <!-- Content -->
            <text x="20" y="67" class="item-text">• 18-Feature Vector Pipeline</text>
            <text x="25" y="85" font-family="'Share Tech Mono', monospace" font-size="9.5px" fill="#f9d423">[Q1-Q5, EAR/MAR ratios, sentiment %]</text>
            
            <text x="20" y="112" class="item-text">• StandardScaler normalisation transform</text>
            
            <text x="20" y="137" class="item-text">• CatBoost Continuous Regressor Inference</text>
            <text x="25" y="155" class="mono-text" style="fill:#ff4e50;">R² Score: 95.76%  |  RMSE: 0.17</text>
            
            <text x="20" y="182" class="item-text">• Output: Burnout Score (Scale: 0.0 - 4.0)</text>
            <text x="25" y="196" font-family="'Share Tech Mono', monospace" font-size="9.5px" fill="#ff4e50">TARGET: clip(base_score + bio_factor, 0, 4)</text>
        </g>

        <!-- ==================== NODE 3: SUPABASE DATABASE (MIDDLE BOTTOM) ==================== -->
        <g transform="translate(450, 390)">
            <rect width="280" height="220" rx="16" ry="16" class="node-bg" stroke="url(#grad-cyan)" stroke-width="2" />
            
            <!-- Header -->
            <rect width="280" height="42" rx="16" ry="16" fill="#14222a" />
            <rect y="32" width="280" height="10" fill="#14222a" />
            <circle cx="20" cy="21" r="5" fill="#00f2fe" />
            <text x="35" y="26" class="header-text">SUPABASE CLOUD STORAGE</text>
            <text x="35" y="37" class="subheader-text">RELATIONAL POSTGRES DATABASE</text>
            <line x1="0" y1="42" x2="280" y2="42" stroke="#20353f" stroke-width="1.5" />

            <!-- Content -->
            <!-- Table 1 -->
            <rect x="15" y="55" width="250" height="65" rx="6" ry="6" fill="#151d24" stroke="#20333f" stroke-width="1" />
            <text x="25" y="72" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="10.5px" fill="#00f2fe">assessments TABLE</text>
            <text x="25" y="90" class="item-text">Log: user_id, answers, ear, mar, emo_pos,</text>
            <text x="25" y="106" class="item-text">emo_neg, voice_transcript, burnout_score</text>

            <!-- Table 2 -->
            <rect x="15" y="132" width="250" height="65" rx="6" ry="6" fill="#151d24" stroke="#20333f" stroke-width="1" />
            <text x="25" y="149" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="10.5px" fill="#4facfe">user_profiles & auth TABLES</text>
            <text x="25" y="167" class="item-text">Stores registration details, tokens,</text>
            <text x="25" y="183" class="item-text">and historical session profiles</text>
        </g>

        <!-- ==================== NODE 4: FASTAPI / COLAB BACKEND (RIGHT) ==================== -->
        <g transform="translate(840, 130)">
            <rect width="310" height="480" rx="16" ry="16" class="node-bg" stroke="url(#grad-emerald)" stroke-width="2" />
            
            <!-- Header -->
            <rect width="310" height="42" rx="16" ry="16" fill="#13231c" />
            <rect y="32" width="310" height="10" fill="#13231c" />
            <circle cx="20" cy="21" r="5" fill="#10b981" />
            <text x="35" y="26" class="header-text">COLAB / FASTAPI BACKEND</text>
            <text x="35" y="37" class="subheader-text">SECURE TUNNELED INFERENCE HOST</text>
            <line x1="0" y1="42" x2="310" y2="42" stroke="#1d382b" stroke-width="1.5" />

            <!-- Content -->
            <!-- Tunnel -->
            <rect x="15" y="60" width="280" height="60" rx="8" ry="8" fill="#131e1a" stroke="#1d3429" stroke-width="1" />
            <text x="30" y="80" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#10b981">NGROK SECURE TUNNEL</text>
            <text x="30" y="100" class="item-text">Forwards local Colab server to public HTTPS</text>

            <!-- FastAPI Server -->
            <rect x="15" y="132" width="280" height="135" rx="8" ry="8" fill="#131e1a" stroke="#1d3429" stroke-width="1" />
            <text x="30" y="152" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#059669">FASTAPI INFERENCE API</text>
            <text x="30" y="175" class="item-text">• POST /v1/chat/completions endpoint</text>
            <text x="30" y="193" class="item-text">• Context Injection layer reads latest metrics</text>
            <text x="30" y="211" class="item-text">• Automatic CBT system-prompt assembly</text>
            <text x="30" y="229" class="item-text">• Combines survey + biometric signals</text>
            <text x="30" y="250" class="mono-text">Content-Type: application/json</text>

            <!-- Model Qwen -->
            <rect x="15" y="280" width="280" height="180" rx="8" ry="8" fill="#131e1a" stroke="#1d3429" stroke-width="1" />
            <text x="30" y="302" font-family="'Plus Jakarta Sans', sans-serif" font-weight="800" font-size="11px" fill="#10b981">FINE-TUNED CBT QWEN MODEL</text>
            <text x="30" y="325" font-family="'Share Tech Mono', monospace" font-size="11px" fill="#10b981">kritika53245/mindhaven-cbt-qwen</text>
            <text x="30" y="347" class="item-text">• Fine-tuned offline on CounselChat + CBT FAQs</text>
            <text x="30" y="365" class="item-text">• Transfer learning via QLoRA adapters</text>
            <text x="30" y="383" class="item-text">• Specialized Cognitive Behavioral Therapy</text>
            <text x="30" y="401" class="item-text">• Evaluates distortion, validates emotions,</text>
            <text x="30" y="419" class="item-text">  and yields micro-action recovery plans</text>
            <text x="30" y="445" font-family="'Share Tech Mono', monospace" font-size="9.5px" fill="#10b981">MODEL INF: LLAMA-3.3 / QWEN BASE</text>
        </g>

        <!-- ==================== FLOW LINES & ARROWS ==================== -->
        <!-- 1. Edge to CatBoost (Feature Vector) -->
        <path d="M 350,230 L 450,230" class="connector-line" stroke="#ff8f00" marker-end="url(#arrow-orange)" />
        <text x="400" y="222" class="label-text" text-anchor="middle">Sends 18-Feature Vector</text>

        <!-- 2. Edge to Supabase (Saves raw biometric logs) -->
        <path d="M 350,470 L 450,470" class="connector-line" stroke="#00f2fe" marker-end="url(#arrow-cyan)" />
        <text x="400" y="462" class="label-text" text-anchor="middle">Logs raw biometrics</text>

        <!-- 3. CatBoost to Supabase (Saves score) -->
        <path d="M 590,340 L 590,390" class="solid-connector" stroke="#ff4e50" marker-end="url(#arrow-cyan)" />
        <text x="600" y="370" class="label-text" style="fill:#ff4e50;">Logs Burnout Score (0.0-4.0)</text>

        <!-- 4. Supabase to FastAPI (Reads context) -->
        <path d="M 730,500 L 840,500" class="connector-line" stroke="#10b981" marker-end="url(#arrow-emerald)" />
        <text x="785" y="492" class="label-text" text-anchor="middle">Injects telemetry context</text>

        <!-- 5. Edge to FastAPI Request (Up and over) -->
        <path d="M 200,130 L 200,105 L 995,105 L 995,130" class="solid-connector" stroke="#8455ef" marker-end="url(#arrow-emerald)" />
        <text x="597" y="101" class="label-text" text-anchor="middle" style="fill:#da77f2;">Queries CBT Chatbot (User input text prompt)</text>

        <!-- 6. FastAPI back to Edge (Down and around) -->
        <path d="M 995,610 L 995,640 L 200,640 L 200,610" class="solid-connector" stroke="#10b981" marker-end="url(#arrow-purple)" />
        <text x="597" y="652" class="label-text" text-anchor="middle" style="fill:#10b981;">Returns empathetic CBT chatbot suggestions</text>
    </svg>
</body>
</html>
"""

# Save html content to a temp file
temp_file = 'artifacts/temp_architecture.html'
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print("Temp SVG HTML file written.")

# Set up Selenium
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1200,700')
chrome_options.add_argument('--hide-scrollbars')

print("Starting Selenium web driver...")
driver = webdriver.Chrome(options=chrome_options)
try:
    # Open the local HTML file
    file_path = os.path.abspath(temp_file)
    print(f"Opening local page: file:///{file_path}")
    driver.get(f"file:///{file_path}")
    
    # Wait for rendering and font loading
    time.sleep(3)
    
    # Capture screenshot
    output_png = 'artifacts/system_architecture.png'
    print(f"Saving high-res screenshot to {output_png}...")
    driver.save_screenshot(output_png)
    print("Screenshot saved successfully!")
finally:
    driver.quit()

# Clean up temp file
if os.path.exists(temp_file):
    os.remove(temp_file)
    print("Temporary HTML file removed.")
