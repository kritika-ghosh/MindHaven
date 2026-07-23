import os
import json
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama
from huggingface_hub import hf_hub_download

app = FastAPI(title="MindHaven CBT Chatbot API")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
GGUF_REPO = os.getenv("GGUF_REPO", "kritika53245/mindhaven-cbt-qwen-gguf")
GGUF_FILE = os.getenv("GGUF_FILE", "mindhaven-cbt-qwen-Q4_K_M.gguf")

print("Downloading and initializing GGUF model...")
model_path = hf_hub_download(repo_id=GGUF_REPO, filename=GGUF_FILE)

# Initialize Llama engine (Optimized for HF 2 vCPU Basic Space)
llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=2,
    verbose=False
)
print("Model loaded successfully into RAM!")

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = 512
    stream: bool = False

@app.get("/health")
def health():
    """Keep-alive ping target"""
    return {"status": "online", "model": GGUF_FILE}

@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequest):
    formatted_messages = [m.model_dump() for m in req.messages]

    if req.stream:
        def stream_generator():
            response_stream = llm.create_chat_completion(
                messages=formatted_messages,
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                stream=True
            )
            for chunk in response_stream:
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(stream_generator(), media_type="text/event-stream")

    # Non-streaming response
    response = llm.create_chat_completion(
        messages=formatted_messages,
        temperature=req.temperature,
        max_tokens=req.max_tokens,
        stream=False
    )
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
