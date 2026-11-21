import type { Question } from "../types/question";
const API = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:5000/api";
export async function getQuestions(): Promise<Question[]> {
  const response = await fetch(`${API}/questions`);
  if (!response.ok) throw new Error(`API request failed: ${response.status}`);
  return response.json() as Promise<Question[]>;
}
