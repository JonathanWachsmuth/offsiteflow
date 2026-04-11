// api.js — Axios instance pointing at the correct backend
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000, // 2 minutes — LLM calls can take 60-90s
})

export default api
