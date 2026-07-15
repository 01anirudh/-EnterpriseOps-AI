import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

axios.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

interface User {
  id: string
  name: string
  email: string
  role: string
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string, role?: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,

      login: async (email, password) => {
        const params = new URLSearchParams()
        params.append('username', email)
        params.append('password', password)
        const res = await axios.post('/api/auth/login', params, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        })
        const { access_token, user_id, name, role } = res.data
        axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
        set({
          token: access_token,
          user: { id: user_id, name, email, role },
          isAuthenticated: true,
        })
      },

      register: async (name, email, password, role = 'user') => {
        await axios.post('/api/auth/register', { name, email, password, role })
      },

      logout: () => {
        delete axios.defaults.headers.common['Authorization']
        set({ token: null, user: null, isAuthenticated: false })
      },
    }),
    {
      name: 'auth-storage',
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          axios.defaults.headers.common['Authorization'] = `Bearer ${state.token}`
        }
      },
    }
  )
)
