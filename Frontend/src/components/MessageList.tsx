import { ScrollArea } from "@/components/ui/scroll-area"
import { Button } from "@/components/ui/button"

interface Message {
  role: "user" | "assistant"
  content: string
}

interface MessageListProps {
  messages: Message[]
  onSendMessage: (message: string) => void
}

const dummyQuestions = [
  "What are the admission requirements?",
  "How do I apply for financial aid?",
  "When is the application deadline?",
  "What majors are offered?",
]

export function MessageList({ messages, onSendMessage }: MessageListProps) {
  return (
    <ScrollArea className="h-[500px] pr-4">
      {messages.length === 0 ? (
        <div className="text-center space-y-6">
          <h2 className="text-2xl font-bold text-primary">Welcome to the University Chatbot!</h2>
          <p className="text-muted-foreground">
            How can I assist you today? Here are some questions you might want to ask:
          </p>
          <div className="space-y-2">
            {dummyQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                className="w-full justify-start text-left h-auto whitespace-normal"
                onClick={() => onSendMessage(question)}
              >
                {question}
              </Button>
            ))}
          </div>
        </div>
      ) : (
        messages.map((message, index) => (
          <div key={index} className={`mb-4 ${message.role === "user" ? "text-right" : "text-left"}`}>
            <div
              className={`inline-block p-3 rounded-lg max-w-[80%] ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-secondary text-secondary-foreground"
              }`}
            >
              {message.content}
            </div>
          </div>
        ))
      )}
    </ScrollArea>
  )
}

