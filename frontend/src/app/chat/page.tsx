"use client";
import Link from "next/link";
import React from "react";

export type MessageData = {
  role: "user" | "assistant";
  content: string;
};



export default function Chat() {
  const [message, setMessage] = React.useState("");
  const [messages, setMessages] = React.useState<MessageData[]>([
    { role: "assistant", content: "Hello, how can I help you?" },
  ]);

  function handleForm(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if(!message) {
      return;
    }
    setMessages([...messages, { role: "user", content: message }]);
    setMessage("");
  }

  return (
    <div className="relative isolate px-5 lg:px-24 py-2 h-screen overflow-hidden bg-gradient-to-b from-bc-red/15">
      <Link href={"/"} className="py-4 px-2  flex gap-2 items-center">
        <h1 className="text-balance text-xl text-center font-semibold">
          bccs club | 🤖 chat
        </h1>
      </Link>
      <div className="h-4/6 rounded overflow-auto">
        <div className="px-5  py-4 flex-col mt-4 flex gap-3">
          {messages.map(message => (
            <div key={message.content} className={`flex items-center gap-2 ${message.role === "user" ? "justify-end" : ""}`}>
              <div className={`rounded-full bg-black w-8 h-8 ${message.role === "user" && "order-2"} `}/>
              <p className="bg-bc-red/15 rounded-lg p-2">{message.content}</p>
            </div>
          ))}
        </div>
      </div>
      <form onSubmit={handleForm}>
      <input
        required
        onChange={e => setMessage(e.target.value)}
        className="mt-3 bg-bc-red/10 w-full h-12 rounded-xl px-5"
        placeholder="Messages"
        value={message}
        type="text"
      />
      </form>
    </div>
  );
}
