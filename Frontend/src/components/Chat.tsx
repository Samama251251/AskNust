import { useWebSocket } from "../hooks/useWebSocket"
import { MessageList } from "./MessageList"
import { ChatInput } from "./ChatInput"
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card"

export function Chat() {
  const { isConnected, messages, sendMessage } = useWebSocket("ws://localhost:8000/ws")

  return (
    <Card className="w-full max-w-2xl mx-auto bg-card text-card-foreground border-secondary shadow-lg">
      <CardHeader className="border-b border-secondary">
        <CardTitle className="text-2xl font-bold text-center text-primary">University Student Chatbot</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <MessageList messages={messages} onSendMessage={sendMessage} />
      </CardContent>
      <CardFooter className="border-t border-secondary pt-6">
        <ChatInput onSendMessage={sendMessage} />
      </CardFooter>
    </Card>
  )
}

