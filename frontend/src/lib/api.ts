const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function sendChatMessage(
  userId: string,
  message: string,
  history: Array<{ role: string; content: string }>
) {
  const res = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId, message, chat_history: history.slice(-10) }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res;
}

export async function getProfile(userId: string) {
  const res = await fetch(`${API_URL}/profile/${userId}`);
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}
