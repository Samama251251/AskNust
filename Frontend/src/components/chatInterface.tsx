import type React from "react"
import { useState } from "react"
import ChatWindow from "./chatwindow"
import { PulseLoader } from "react-spinners"

interface Message {
  text: string
  sender: "user" | "bot"
}

interface Chat {
  messages: Message[]
}

const ChatInterface: React.FC = () => {
  const [chat, setChat] = useState<Chat>({ messages: [] })
  const [isWaiting, setIsWaiting] = useState<boolean>(false)

  const handleSendMessage = (message: string) => {
    const updatedChat: Chat = {
      messages: [...chat.messages, { text: message, sender: "user" }],
    }
  
    setChat(updatedChat)
    setIsWaiting(true)
  
    try {
      const chatHistoryString = JSON.stringify(
        updatedChat.messages.map(msg => ({
          content: msg.text,
          role: msg.sender === 'user' ? 'user' : 'assistant'
        }))
      );
  
      const url = new URL('https://nustchatbot.samama.live/chat-stream');
      url.searchParams.append('prompt', message);
      url.searchParams.append('chat_history', chatHistoryString);
      
      const eventSource = new EventSource(url.toString());
      
      // Add a new bot message placeholder.
      setChat(prevChat => ({
        messages: [
          ...prevChat.messages,
          { text: '', sender: 'bot' }
        ]
      }));
      
      let streamingStarted = false;
  
      eventSource.onmessage = (event) => {
        try {
          // Toggle waiting off only when the first message is received.
          if (!streamingStarted) {
            streamingStarted = true;
            setIsWaiting(false);
          }
          const parsedData = JSON.parse(event.data);
          if (parsedData.content) {
            setChat(prevChat => {
              const messages = [...prevChat.messages];
              const lastMessage = messages[messages.length - 1];
              if (lastMessage && lastMessage.sender === 'bot') {
                messages[messages.length - 1] = {
                  ...lastMessage,
                  text: lastMessage.text + parsedData.content
                };
              }
              return { messages };
            });
          }
        } catch (error) {
          console.error('Error parsing SSE data:', error);
        }
      };
  
      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
      };
  
      return () => {
        eventSource.close();
      };
  
    } catch (error) {
      console.error('Error setting up SSE:', error);
    }
  }

  return (
    <div className="h-screen bg-gray-100 relative">
      <ChatWindow chat={chat} onSendMessage={handleSendMessage} />
      {isWaiting && (
        <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 bg-white rounded-full px-4 py-2 shadow-lg flex items-center gap-2">
          <PulseLoader color="#4B5563" size={8} />
          <span className="text-gray-600 text-sm">AskNust is Thinking</span>
        </div>
      )}
    </div>
  )
}

export default ChatInterface