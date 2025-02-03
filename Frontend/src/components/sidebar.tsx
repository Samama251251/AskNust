import type React from "react"

interface Message {
  text: string
  sender: "user" | "bot"
}

interface Chat {
  id: number
  title: string
  messages: Message[]
}

interface SidebarProps {
  chatHistory: Chat[]
  activeChat: Chat | null
  onSelectChat: (chat: Chat) => void
  onNewChat: () => void
}

const Sidebar: React.FC<SidebarProps> = ({ chatHistory, activeChat, onSelectChat, onNewChat }) => {
  return (
    <div className="w-64 bg-white h-full shadow-md flex flex-col">
      <div className="p-4">
        <button
          onClick={onNewChat}
          className="w-full py-2 px-4 bg-black text-white rounded-full hover:bg-gray-800 transition-colors duration-300"
        >
          New Chat
        </button>
      </div>
      <div className="flex-grow overflow-y-auto">
        {chatHistory.map((chat) => (
          <div
            key={chat.id}
            className={`p-3 cursor-pointer hover:bg-gray-100 ${
              activeChat && activeChat.id === chat.id ? "bg-gray-200" : ""
            }`}
            onClick={() => onSelectChat(chat)}
          >
            <h3 className="font-medium truncate">{chat.title}</h3>
            <p className="text-sm text-gray-500 truncate">
              {chat.messages[chat.messages.length - 1]?.text || "No messages yet"}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Sidebar

