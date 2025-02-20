import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from googlesearch import search
import google.generativeai as genai
from typing import List
import time

class UniversityChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with your Google API key."""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite-preview-02-05')
        self.crawler = None
        
    async def __aenter__(self):
        """Initialize the crawler when entering context."""
        self.crawler = AsyncWebCrawler()
        await self.crawler.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup crawler when exiting context."""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    def search_google(self, query: str, num_results: int = 2) -> List[str]:
        """Search Google and return the top URLs."""
        urls = []
        try:
            search_results = search(query, num_results =num_results)
            urls = list(search_results)
            time.sleep(0.2)  # Add delay between searches
        except Exception as e:
            print(f"Error during Google search: {e}")
        return urls

    async def scrape_webpage(self, url: str) -> str:
        """Scrape content from a webpage using crawl4ai."""
        try:
            # if "nust.edu.pk" not in url:
            #     print(f"Skipping non-NUST URL: {url}")
            #     return ""
                
            if self.crawler:
                run_cfg = CrawlerRunConfig(only_text=True)
                result = await self.crawler.arun(
                    url=url,
                    config=run_cfg,
                )
                return result.markdown_v2 if result else ""
            else:
                print("Crawler not initialized")
                return ""
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""

    async def get_context(self, query: str) -> str:
        """Get context by searching Google and scraping top results."""
        urls = self.search_google(query)
        context = []
        
        for url in urls:
            content = await self.scrape_webpage(url)
            if content:
                context.append(f"Source ({url}):\n{content}\n")
        return "\n".join(context)

    async def get_response(self, query: str) -> str:
        """Get chatbot response using searched context."""
        context = await self.get_context(query)
        
        try:
            prompt = f"""**System Instructions**:
You are a helpful university chatbot. Use the provided context to answer questions.
If the context doesn't contain relevant information, say so and provide a general response based on your knowledge.
Always cite sources when using information from the context.

**Context**:
{context}

**Question**:
{query}

Please provide a helpful response using the above context and your knowledge."""
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            if response.parts:
                return response.text
            return "Sorry, I couldn't generate a response for that question."
            
        except Exception as e:
            print(f"Error getting Gemini response: {e}")
            return "I encountered an error processing your question. Please try again."

class UniversityChatbotWithMemory(UniversityChatbot):
    def __init__(self, api_key: str):
        """Initialize the chatbot with memory of conversation history."""
        super().__init__(api_key)
        self.chat = None

    async def get_response(self, query: str) -> str:
        """Get chatbot response with conversation history."""
        context = await self.get_context(query)
        
        try:
            prompt = f"""**System Instructions**:
You are a helpful university chatbot. Use the provided context to answer questions.
Maintain context from previous conversations when relevant.
Always cite sources when using information from the context.
If context is unavailable, provide general information.

**Context**:
{context}

**Question**:
{query}

Please provide a helpful response considering both current context and conversation history."""
            
            if self.chat is None:
                self.chat = self.model.start_chat(history=[])
            
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.chat.send_message(prompt)
            )
            
            if response.parts:
                return response.text
            return "Sorry, I couldn't generate a response for that question."
            
        except Exception as e:
            print(f"Error getting Gemini response: {e}")
            return "I encountered an error processing your question. Please try again."

async def main():
    api_key = "AIzaSyCcZp2pD7_zlhwJl9nHGPBI-8YQOSSCFsA"
    use_memory = False
    
    async with (UniversityChatbotWithMemory(api_key) if use_memory else UniversityChatbot(api_key)) as chatbot:
        print("University Chatbot (type 'quit' to exit)")
        print("-" * 50)
        
        while True:
            query = input("\nYour question: ")
            if query.lower() == 'quit':
                break
                
            print("\nSearching and processing...")
            response = await chatbot.get_response(query)
            print("\nChatbot:", response)

if __name__ == "__main__":
    asyncio.run(main())