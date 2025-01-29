import { useState, useEffect, useCallback } from "react"

export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; content: string }[]>([])

  useEffect(() => {
    const ws = new WebSocket(url)

    ws.onopen = () => {
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      setMessages((prevMessages) => [...prevMessages, message])
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    setSocket(ws)

    return () => {
      ws.close()
    }
  }, [url])

  const sendMessage = useCallback(
    (content: string) => {
      if (socket && isConnected) {
        const message = { role: "user" as const, content }
        socket.send(JSON.stringify(message))
        setMessages((prevMessages) => [...prevMessages, message])
      }
    },
    [socket, isConnected],
  )

  return { isConnected, messages, sendMessage }
}

