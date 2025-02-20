import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from googlesearch import search
from openai import OpenAI
from typing import List
import time
import random

class UniversityChatbot:
    def __init__(self, api_key: str):
        """Initialize the chatbot with your OpenAI API key."""
        self.client = OpenAI(api_key=api_key)
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

    def search_google(self, query: str, num_results: int = 3) -> List[str]:
        """Search Google and return the top URLs."""
        urls = []
        try:
            search_results = search(query, num=num_results, stop=num_results)
            urls = list(search_results)
            # Add delay between searches
            time.sleep(0.2)
        except Exception as e:
            print(f"Error during Google search: {e}")
        print("I am done")
        return urls

    async def scrape_webpage(self, url: str) -> str:
        """Scrape content from a webpage using crawl4ai."""
        try:
            # Skip if URL is not from NUST website
            print("I am starting")
            if "nust.edu.pk" not in url:
                print(f"Skipping non-NUST URL: {url}")
                return ""
                
            if self.crawler:
                # Use existing crawler instance
                run_cfg = CrawlerRunConfig(only_text=True)
                result = await self.crawler.arun(
                    url=url,
                    config=run_cfg,
                )
                
                if result:
                    return result.markdown_v2
                else:
                    print(f"Failed to crawl: {url}")
                    return ""
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
        # Get context from web search
        context = await self.get_context(query)
        
        try:
            # Create completion with GPT
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",  # or gpt-3.5-turbo for faster/cheaper responses
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful university chatbot. Use the provided context to answer questions.
                        If the context doesn't contain relevant information, say so and provide a general response based on your knowledge.
                        Always cite sources when using information from the context."""
                    },
                    {
                        "role": "user",
                        "content": f"""Context:
                        {context}
                        
                        Question: {query}
                        
                        Please provide a helpful response using the above context and your knowledge."""
                    }
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting GPT response: {e}")
            return "I apologize, but I encountered an error processing your question. Please try again."

class UniversityChatbotWithMemory(UniversityChatbot):
    def __init__(self, api_key: str):
        """Initialize the chatbot with memory of conversation history."""
        super().__init__(api_key)
        self.conversation_history = []

    async def get_response(self, query: str) -> str:
        """Get chatbot response with conversation history."""
        # Get context from web search
        context = await self.get_context(query)
        
        try:
            # Prepare messages including conversation history
            messages = [
                {
                    "role": "system",
                    "content": """You are a helpful university chatbot. Use the provided context to answer questions.
                    If the context doesn't contain relevant information, say so and provide a general response based on your knowledge.
                    Always cite sources when using information from the context.
                    Maintain context from the conversation history when relevant."""
                }
            ]
            
            # Add conversation history
            messages.extend(self.conversation_history)
            
            # Add current query with context
            messages.append({
                "role": "user",
                "content": f"""Context:
                {context}
                
                Question: {query}
                
                Please provide a helpful response using the above context, conversation history, and your knowledge."""
            })
            
            # Get response from GPT
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": query
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.choices[0].message.content
            })
            
            # Keep only last 10 messages to manage context length
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error getting GPT response: {e}")
            return "I apologize, but I encountered an error processing your question. Please try again."

# Modify the main function to use async context manager
async def main():
    api_key = "sk-SNmrvRHrImV6BNABsxAgCgpVQw1dIgsGcVQsDbeMdMT3BlbkFJkE4nudEUff3LhipEAFd4TU4EK4NCC3oorbInBsPikA"
    use_memory = False
    
    # Create chatbot instance using async context manager
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