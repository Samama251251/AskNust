# AskNUST - AI Chatbot with RAG + Web Crawling  

AskNUST is an AI-powered chatbot designed to provide real-time and reliable answers to university-related queries. Unlike traditional RAG-based chatbots that rely solely on pre-indexed documents, AskNUST integrates **web crawling** to fetch real-time updates from official university sources, ensuring accurate and up-to-date responses.  

## How It Works  

1. **Knowledge Storage**: University documents are indexed and stored in **PineconeDB** for efficient retrieval.  
2. **Live Data Fetching**: A **web crawler** extracts real-time information from university websites.  
3. **Hybrid RAG Approach**: Combines stored knowledge with live data to generate **contextually relevant** answers.  
4. **Real-Time Streaming**: Delivers progressively generated responses for a smooth user experience.  

## Tech Stack  

- **Frontend**: React (deployed on Vercel)  
- **Backend**: FastAPI (hosted on AWS EC2), LangChain, MongoDB  
- **Vector Storage**: PineconeDB for efficient semantic search  
- **Live Data Retrieval**: Web crawler running on AWS EC2  

The chatbot is live at **[AskNUST](https://lnkd.in/dwT8d_Va)**.  

