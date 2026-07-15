import { create } from 'zustand'
import axios from 'axios'

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  embedding_status: string
  chunk_count: number
  uploaded_at: string
}

interface DocumentState {
  documents: Document[]
  uploading: boolean
  fetchDocuments: () => Promise<void>
  uploadDocument: (file: File, onProgress?: (pct: number) => void) => Promise<void>
  deleteDocument: (id: string) => Promise<void>
}

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  uploading: false,

  fetchDocuments: async () => {
    const res = await axios.get('/api/documents')
    set({ documents: res.data })
  },

  uploadDocument: async (file, onProgress) => {
    set({ uploading: true })
    const formData = new FormData()
    formData.append('file', file)
    try {
      await axios.post('/api/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total && onProgress) {
            onProgress(Math.round((e.loaded / e.total) * 100))
          }
        },
      })
      await get().fetchDocuments()
    } finally {
      set({ uploading: false })
    }
  },

  deleteDocument: async (id) => {
    await axios.delete(`/api/documents/${id}`)
    set((state) => ({
      documents: state.documents.filter((d) => d.id !== id),
    }))
  },
}))
