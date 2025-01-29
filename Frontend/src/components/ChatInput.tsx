import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { SendHorizontal } from "lucide-react"

interface ChatInputProps {
  onSendMessage: (message: string) => void
}

export function ChatInput({ onSendMessage }: ChatInputProps) {
  const [input, setInput] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSendMessage(input)
      setInput("")
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex space-x-2 w-full">
      <Input
        type="text"
        placeholder="Type your message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="flex-grow bg-secondary text-secondary-foreground"
      />
      <Button type="submit" size="icon" className="bg-primary hover:bg-primary/90">
        <SendHorizontal className="h-4 w-4" />
      </Button>
    </form>
  )
}

