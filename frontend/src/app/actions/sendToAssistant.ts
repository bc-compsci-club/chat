'use server'
import { MessageData } from "../chat/page";

export default async function sendToAssistant(messages: MessageData[]) {
  const ctx = await getAssistantResponse(messages);
  console.log(ctx)
}


async function getAssistantResponse(messages: MessageData[]) {
  const response = await fetch("http://127.0.0.1:5000/api/v1/llm", {
    method: "POST",
    body: JSON.stringify(messages),
    headers: {
      "Content-Type": "application/json",
    },
  });
  
  return response;
}
