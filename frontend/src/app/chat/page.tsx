"use client";
import Link from "next/link";
import React from "react";

export type MessageData = {
  role: "user" | "assistant";
  content: string;
};

export default function Chat() {
  const [message, setMessage] = React.useState("");
  const [messages, setMessages] = React.useState<MessageData[]>([]);

  
  function isScrolledToBottom(element: HTMLDivElement | null) {
    if(element) {
      element.scroll({ top: element.scrollHeight, behavior: "smooth" });
    }
  }

  async function handleForm(e: React.FormEvent) {
    e.preventDefault()
    setMessage("");
    setMessages((messages) => [
      ...messages,
      { role: "user", content: message },
      { role: "assistant", content: "Thinking..." },
    ]);
    console.time("fetch");
    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/llm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify([...messages, { role: "user", content: message }]),
    });
    if(!response.body) return;
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;
    while (true) {
      const { value, done } = await reader.read();
      const text = decoder.decode(value, { stream: true });

      setMessages((messages) => {
        let lastMessage = messages[messages.length - 1];
        let otherMessages = messages.slice(0, messages.length - 1);
        return [
          ...otherMessages,
          {
            ...lastMessage,
            content: lastMessage.content === "Thinking..." ? text : lastMessage.content + text,
          },
        ];
      });
      if (done) break;
    }
    console.timeEnd("fetch");
  }
  return (
    <div className="relative isolate px-5 lg:px-24 py-2 h-full bg-gradient-to-b from-bc-red/15">
      <Link href={"/"} className="py-4 px-2 w-fit flex gap-2 items-center">
        <h1 className="text-balance text-xl text-center font-semibold">
          bccs club | 🤖 chat
        </h1>
      </Link>
      <div ref={isScrolledToBottom} className={`h-4/5 rounded overflow-auto  ${messages.length > 0 ? "block" : "hidden"}`}>
        <div className="px-5 py-4 flex-col mt-4 flex gap-3">
          {messages.map((message, i) => (
            <div key={i} className={`flex items-center gap-4 ${message.role === "user" ? "justify-end" : ""}`}>
              <div className={`rounded-full px-4 bg-red-200 w-8 h-8 ${message.role === "user" && "order-2"} `}/>
              <p className="bg-bc-red/15 rounded-lg p-2">{message.content}</p>
            </div>
          ))}
        </div>
      </div>
      <div className={messages.length === 0 ? "h-5/6 w-full flex items-center gap-2 flex-col justify-center" : "block"}> 
      <div className={`${messages.length === 0 ? "w-full animate-typing overflow-hidden whitespace-nowrap flex items-center justify-center font-bold text-2xl" : "hidden"}`}>What can I help you with?</div>
      <form className="w-full" onSubmit={handleForm}>
      <input 
        onChange={e => setMessage(e.target.value)}
        required
        onInvalid={(e) => e.preventDefault()}
        className="mt-3 bg-bc-red/10 w-full h-12 rounded-xl px-5 focus:outline-none"
        placeholder="Enter your message..."
        value={message}
        type="text"
      />
      </form>
      </div>
    </div>
  );
}
