const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
export async function request(path, {token, ...options} = {}) {
  const res = await fetch(`${API}${path}`, {
    ...options,
    headers: {'Content-Type':'application/json', ...(token?{Authorization:`Bearer ${token}`} : {}), ...(options.headers||{})}
  })
  const data = await res.json().catch(()=>({detail:'Unexpected server response'}))
  if (!res.ok) throw new Error(data.detail || 'Request failed')
  return data
}
export {API}
