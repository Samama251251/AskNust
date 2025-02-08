import type React from "react"
import { useState } from "react"
import ChatWindow from "./chatwindow"

interface Message {
  text: string
  sender: "user" | "bot"
}

interface Chat {
  messages: Message[]
}

const ChatInterface: React.FC = () => {
  const [chat, setChat] = useState<Chat>({ messages: [] })

  const handleSendMessage = (message: string) => {
    const updatedChat: Chat = {
      messages: [...chat.messages, { text: message, sender: "user" }],
    }
  
    setChat(updatedChat);
  
    try {
      const chatHistoryString = JSON.stringify(
        updatedChat.messages.map(msg => ({
          content: msg.text,
          role: msg.sender === 'user' ? 'user' : 'assistant'
        }))
      );
  
      const url = new URL('http://localhost:8000/chat-stream');
      url.searchParams.append('prompt', message);
      url.searchParams.append('chat_history', chatHistoryString);
      
      const eventSource = new EventSource(url.toString());
      
      setChat(prevChat => ({
        messages: [
          ...prevChat.messages,
          { text: '', sender: 'bot' }
        ]
      }));
  
      eventSource.onmessage = (event) => {
        try {
          console.log("I am being abused")
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
    <div className="h-screen bg-gray-100">
      <ChatWindow chat={chat} onSendMessage={handleSendMessage} />
    </div>
  )
}

export default ChatInterface

