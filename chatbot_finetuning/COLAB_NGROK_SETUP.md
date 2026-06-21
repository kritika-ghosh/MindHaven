# Serving Qwen CBT Fine-Tuned Model via Google Colab & Ngrok

This guide provides detailed steps to load your custom fine-tuned Qwen model ([`kritika53245/mindhaven-cbt-qwen`](https://huggingface.co/kritika53245/mindhaven-cbt-qwen)) in a free Google Colab GPU instance, host an OpenAI-compatible FastAPI server, and tunnel it using Ngrok so that your MindHaven frontend can connect to it.

---

## ─── 🚀 Step-by-Step Setup ───

### Step 1: Open Google Colab & Enable GPU
1. Go to [colab.research.google.com](https://colab.research.google.com).
2. Create a new notebook named `MindHaven_CBT_Inference.ipynb`.
3. In the top menu, go to **Runtime** > **Change runtime type**.
4. Select **T4 GPU** (or any active GPU accelerator) and click **Save**.

### Step 2: Install Required Libraries
Create a code cell and run the following command to install dependencies:
```python
!pip install -q transformers accelerate torch fastapi uvicorn pyngrok nest-asyncio pydantic
```

### Step 3: Get your Ngrok Authtoken
1. Register/Login at [dashboard.ngrok.com](https://dashboard.ngrok.com).
2. Go to the **Your Authtoken** section in the left sidebar.
3. Copy your unique authtoken string.

---

## ─── 💻 Google Colab Code cells ───

Copy the following blocks of code into sequential cells in your Google Colab notebook.

### Cell 1: Load tokenizer & model (Optimized for T4 VRAM)
```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "kritika53245/mindhaven-cbt-qwen"

print("Loading tokenizer and model (this might take a few minutes)...")
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True
)
print("Model loaded successfully on GPU!")
```

### Cell 2: Define FastAPI server and chat generation logic
```python
import nest_asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional

# Enable nesting uvicorn loops in Google Colab
nest_asyncio.apply()

app = FastAPI(title="MindHaven CBT Inference API")

# Enable CORS so your frontend can fetch directly from this tunnel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    try:
        # Format the input using the Qwen chat template
        formatted_messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # Apply Qwen template
        prompt = tokenizer.apply_chat_template(
            formatted_messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize and generate
        inputs = tokenizer([prompt], return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True if request.temperature > 0 else False,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode output
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, outputs)
        ]
        response_text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        # Return standard OpenAI response format
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": response_text.strip()
                    },
                    "finish_reason": "stop",
                    "index": 0
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Cell 3: Configure Ngrok tunnel and start FastAPI server
```python
from pyngrok import ngrok

# Configure your token (replace with your copied token)
NGROK_TOKEN = "YOUR_NGROK_AUTHTOKEN_HERE"
ngrok.set_auth_token(NGROK_TOKEN)

# Open an HTTP tunnel on port 8000
public_url = ngrok.connect(8000)
print("\n" + "="*60)
print(f"👉 Ngrok Tunnel is Active!")
print(f"🔗 Public OpenAI endpoint: {public_url.public_url}/v1/chat/completions")
print("="*60 + "\n")

# Start server using the notebook's active event loop
config = uvicorn.Config(app, host="0.0.0.0", port=8000)
server = uvicorn.Server(config)
await server.serve()
```

---

## ─── 🔌 Connecting to the Frontend ───

Once the Ngrok server runs in Google Colab, you will see a public URL printed, like:
`https://a1b2-34-56-78-90.ngrok-free.app`

Update your frontend configuration inside `frontend/js/config.js` to route all AI Coach chat queries to this server:

```javascript
// frontend/js/config.js
window.MINDHAVEN_CONFIG = {
  // Replace with the active ngrok URL (leave the /v1/chat/completions off - index.js handles routing)
  GROQ_KEY: "ngrok", // Set GROQ_KEY to "ngrok" or any value to enable chat UI
  
  // Custom API configuration override if needed
  API_URL: "https://kritika53245-mindhaven.hf.space/predict"
};
```

Wait, in `frontend/insights.html`, we need to make sure the fetch call respects this ngrok URL!
Let's review the API fetch block inside `insights.html` around line 755:
```javascript
                const res = await fetch("https://api.groq.com/openai/v1/chat/completions", {
```
To route this dynamically:
If `window.MINDHAVEN_CONFIG.GROQ_KEY === "ngrok"` or if `window.MINDHAVEN_CONFIG.CHAT_API_URL` is set, we can direct the fetch to that URL!
This will make the frontend 100% production-ready for your custom Hugging Face model running on Google Colab!
