"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send } from "lucide-react"

interface Message {
  role: "user" | "assistant"
  content: string
}

const ChatInterface = () => {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")

  const handleSend = async () => {
    if (!input.trim()) return

    const newMessage: Message = { role: "user", content: input }
    setMessages([...messages, newMessage])
    setInput("")

    // TODO: Implement RAG-based response generation here
    const assistantMessage: Message = {
      role: "assistant",
      content: "This is a placeholder response. Implement RAG-based logic here.",
    }
    setMessages((prevMessages) => [...prevMessages, assistantMessage])
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50">
      <ScrollArea className="flex-1 p-4">
        {messages.map((message, index) => (
          <div key={index} className={`mb-4 ${message.role === "user" ? "text-right" : "text-left"}`}>
            <div
              className={`inline-block p-2 rounded-lg ${
                message.role === "user" ? "bg-blue-600 text-white" : "bg-white text-gray-800 border border-gray-300"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
      </ScrollArea>
      <div className="p-4 bg-white border-t">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message here..."
            onKeyPress={(e) => e.key === "Enter" && handleSend()}
          />
          <Button onClick={handleSend}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface

