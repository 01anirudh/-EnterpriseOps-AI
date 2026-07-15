import { create } from 'zustand'
import axios from 'axios'

export interface LogEntry {
  type: string
  agent: string
  status: string
  message: string
  execution_time_ms?: number
  timestamp?: number
  report_path?: string
}

export interface Task {
  id: string
  prompt: string
  status: string
  created_at: string
  completed_at?: string
  result_summary?: string
  report_path?: string
}

interface WorkflowState {
  tasks: Task[]
  activeTaskId: string | null
  logs: LogEntry[]
  isStreaming: boolean
  pendingApprovals: Task[]
  submitWorkflow: (prompt: string) => Promise<string>
  fetchTasks: () => Promise<void>
  fetchPendingApprovals: () => Promise<void>
  approveTask: (taskId: string) => Promise<void>
  rejectTask: (taskId: string) => Promise<void>
  startStreaming: (taskId: string, onLog: (log: LogEntry) => void) => () => void
  clearLogs: () => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  tasks: [],
  activeTaskId: null,
  logs: [],
  isStreaming: false,
  pendingApprovals: [],

  submitWorkflow: async (prompt) => {
    const res = await axios.post('/api/workflow', { prompt })
    const taskId = res.data.task_id
    set({ activeTaskId: taskId, logs: [] })
    await get().fetchTasks()
    return taskId
  },

  fetchTasks: async () => {
    const res = await axios.get('/api/workflow')
    set({ tasks: res.data })
  },

  fetchPendingApprovals: async () => {
    const res = await axios.get('/api/workflow/pending/approvals')
    set({ pendingApprovals: res.data })
  },

  approveTask: async (taskId) => {
    await axios.post(`/api/workflow/${taskId}/approve`)
    await get().fetchPendingApprovals()
    await get().fetchTasks()
  },

  rejectTask: async (taskId) => {
    await axios.post(`/api/workflow/${taskId}/reject`)
    await get().fetchPendingApprovals()
    await get().fetchTasks()
  },

  startStreaming: (taskId, onLog) => {
    set({ isStreaming: true })
    const eventSource = new EventSource(`/api/workflow/stream/${taskId}`, {
    })

    eventSource.onmessage = (e) => {
      try {
        const log: LogEntry = JSON.parse(e.data)
        set((state) => ({ logs: [...state.logs, log] }))
        onLog(log)
        if (log.type === 'completed' || log.type === 'failed' || log.type === 'rejected') {
          eventSource.close()
          set({ isStreaming: false })
        }
      } catch { /* ignore parse errors */ }
    }

    eventSource.onerror = () => {
      eventSource.close()
      set({ isStreaming: false })
    }

    return () => {
      eventSource.close()
      set({ isStreaming: false })
    }
  },

  clearLogs: () => set({ logs: [] }),
}))
