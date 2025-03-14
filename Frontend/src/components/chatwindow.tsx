import React, { useState } from "react"
import ReactMarkdown from "react-markdown"

interface Message {
  text: string
  sender: "user" | "bot"
}

interface Chat {
  messages: Message[]
}

interface ChatWindowProps {
  chat: Chat
  onSendMessage: (message: string) => void
}

const suggestedQuestions: string[] = [
  "Who is the Rector of Nust?",
  "Explain me the fee structre of Nust Hostels",
  "Admission process for Nust?"
]

const ChatWindow: React.FC<ChatWindowProps> = ({ chat, onSendMessage }) => {
  const [message, setMessage] = useState<string>("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim()) {
      onSendMessage(message)
      setMessage("")
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-gray-50">
      <div className="flex-1 overflow-y-auto p-4">
        {chat.messages.length > 0 ? (
          chat.messages.map((msg, index) => (
            <div key={index} className={`mb-4 ${msg.sender === "user" ? "text-right" : "text-left"}`}>
              <div
                className={`inline-block p-3 rounded-lg ${
                  msg.sender === "user" ? "bg-black text-white" : "bg-white text-gray-800 shadow"
                }`}
              >
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))
        ) : (
          <div className="h-full flex flex-col items-center justify-center">
            <h2 className="text-2xl font-bold mb-4">Welcome to Chatbot</h2>
            <p className="text-gray-600 mb-6">Try one of these suggested questions:</p>
            <div className="space-y-2">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  className="block w-full text-left p-2 bg-white rounded-lg shadow hover:bg-gray-100 transition-colors duration-300"
                  onClick={() => onSendMessage(question)}
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="p-4 bg-white shadow-md">
        <div className="flex rounded-full border border-gray-300 overflow-hidden">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 px-4 py-2 focus:outline-none"
          />
          <button
            type="submit"
            className="bg-black text-white px-6 py-2 font-medium hover:bg-gray-800 transition-colors duration-300"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatWindow

