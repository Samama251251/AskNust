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
      setTimeout(() => {
        const botResponse: Message = { text: "This is a simulated response.", sender: "bot" }
        const updatedChatWithResponse: Chat = {
          ...updatedChat,
          messages: [...updatedChat.messages, botResponse],
        }
        setChatHistory(chatHistory.map((chat) => (chat.id === activeChat.id ? updatedChatWithResponse : chat)))
        setActiveChat(updatedChatWithResponse)
      }, 1000)
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

