// Thin wrapper around the backend REST API. All paths are relative to /api,
// which Vite proxies to the FastAPI server in development.

const BASE = '/api'

async function request(path, options) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    let detail = response.statusText
    try {
      detail = (await response.json()).detail ?? detail
    } catch {
      /* response had no JSON body */
    }
    throw new Error(detail)
  }
  return response.status === 204 ? null : response.json()
}

export const api = {
  nextQuestion: (subgroup, excludeId) => {
    const exclude = excludeId != null ? `&exclude=${excludeId}` : ''
    return request(`/questions/next?subgroup=${encodeURIComponent(subgroup)}${exclude}`)
  },
  submitAnswer: (payload) =>
    request('/answers', { method: 'POST', body: JSON.stringify(payload) }),
  progress: () => request('/progress'),
  writingPrompts: () => request('/writing/prompts'),
  writingPrompt: (id) => request(`/writing/prompts/${id}`),
  submitEssay: (payload) =>
    request('/writing/essays', { method: 'POST', body: JSON.stringify(payload) }),
}
