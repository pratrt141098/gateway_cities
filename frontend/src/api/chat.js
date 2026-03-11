export async function sendChat(question) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  })

  if (!res.ok) {
    throw new Error(`Chat request failed with status ${res.status}`)
  }

  return res.json()
}

