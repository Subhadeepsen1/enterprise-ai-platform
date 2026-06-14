import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      loading: false,
      error: null,

      login: async (username, password) => {
        set({ loading: true, error: null })
        try {
          const form = new FormData()
          form.append('username', username)
          form.append('password', password)
          const { data } = await api.post('/auth/login', form, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          })
          api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
          set({ token: data.access_token, user: data.user, loading: false })
          return true
        } catch (err) {
          set({ error: err.response?.data?.detail || 'Login failed', loading: false })
          return false
        }
      },

      logout: () => {
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, error: null })
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'enterprise-ai-auth',
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${state.token}`
        }
      },
    }
  )
)
