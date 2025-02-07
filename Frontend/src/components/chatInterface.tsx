import type React from "react"
import { useState } from "react"
import Sidebar from "./sidebar"
import ChatWindow from "./chatwindow"

interface Message {
  text: string
  sender: "user" | "bot"
}

interface Chat {
  id: number
  title: string
  messages: Message[]
}

const ChatInterface: React.FC = () => {
  const [activeChat, setActiveChat] = useState<Chat | null>(null)
  const [chatHistory, setChatHistory] = useState<Chat[]>([])

  const handleNewChat = () => {
    const newChat: Chat = {
      id: Date.now(),
      title: "New Chat",
      messages: [],
    }
    setChatHistory([newChat, ...chatHistory])
    setActiveChat(newChat)
  }

  const handleSendMessage = (message: string) => {
    if (activeChat) {
      const updatedChat: Chat = {
        ...activeChat,
        messages: [...activeChat.messages, { text: message, sender: "user" }],
      }
      setChatHistory(chatHistory.map((chat) => (chat.id === activeChat.id ? updatedChat : chat)))
      setActiveChat(updatedChat)
      
      // Connect to SSE endpoint
      const eventSource = new EventSource('http://localhost:8080/chat');
      
      // Handle incoming message chunks
      eventSource.onmessage = (event) => {
        const botResponse: Message = { 
          text: event.data, 
          sender: "bot" 
        }
        
        setActiveChat(prevChat => {
          if (!prevChat) return null;
          const updatedChatWithResponse = {
            ...prevChat,
            messages: [...prevChat.messages, botResponse],
          }
          setChatHistory(prev => 
            prev.map(chat => 
              chat.id === prevChat.id ? updatedChatWithResponse : chat
            )
          )
          return updatedChatWithResponse;
        })
      };

      // Handle any errors
      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
      };

      // Clean up the connection when component unmounts
      return () => {
        eventSource.close();
      };
    }
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar
        chatHistory={chatHistory}
        activeChat={activeChat}
        onSelectChat={setActiveChat}
        onNewChat={handleNewChat}
      />
      <ChatWindow activeChat={activeChat} onSendMessage={handleSendMessage} />
    </div>
  )
}

export default ChatInterface

