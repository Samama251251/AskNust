import json
import uuid
import asyncio
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import google.generativeai as genai
from googlesearch import search
from typing import List


router = APIRouter()
def search_google(query: str, num_results: int = 3) -> List[str]:
    urls = []
    try:
        search_results = search(query, num_results=num_results)
        urls = list(search_results)
        time.sleep(0.2)
    except Exception as e:
        print(f"Error during Google search: {e}")
    return urls

async def generate_streaming_response(prompt: str, chatbot: AsyncWebCrawler):
    try:
        message_id = str(uuid.uuid4())
        model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
        processing_message = {
            "id": message_id,
            "role": "assistant",
            "content": ""
        }
        yield f"data: {json.dumps(processing_message)}\n\n"
        
        urls = search_google(prompt)
        context_parts = []
        for url in urls:
            try:
                run_cfg = CrawlerRunConfig(only_text=True)
                result = await chatbot.arun(url=url, config=run_cfg)
                if result and result.markdown_v2:
                    context_parts.append(f"Source ({url}):\n{result.markdown_v2}\n")
            except Exception as e:
                print(f"Error scraping {url}: {e}")
                continue
        
        context = "\n".join(context_parts)
        prompt_template = f"""**System Instructions**:
You are a helpful university chatbot. Use the provided context to answer questions.
If the context doesn't contain relevant information, say I do not have enough information to answer this question and avoid citing sources.
**Context**:
{context}

**Question**:
{prompt}

Please provide a helpful response."""
        
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt_template)
        )
        
        if response.text:
            chunk_size = 100
            chunks = [response.text[i:i + chunk_size] for i in range(0, len(response.text), chunk_size)]
            for chunk in chunks:
                message = {
                    "id": message_id,
                    "role": "assistant",
                    "content": chunk
                }
                yield f"data: {json.dumps(message)}\n\n"
                await asyncio.sleep(0.02)
        else:
            error_message = {
                "id": message_id,
                "role": "assistant",
                "content": "Sorry, I couldn't generate a response."
            }
            yield f"data: {json.dumps(error_message)}\n\n"
            
    except Exception as e:
        error_message = {
            "id": str(uuid.uuid4()),
            "role": "assistant",
            "content": f"Error: {str(e)}"
        }
        yield f"data: {json.dumps(error_message)}\n\n"

@router.get("/chat-stream")
async def chat_stream(prompt: str = None):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt parameter is required")
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*"
    }
    from main import chatbot  # or use Dependency Injection to get the chatbot instance
    return StreamingResponse(
        generate_streaming_response(prompt, chatbot),
        media_type="text/event-stream",
        headers=headers
    )