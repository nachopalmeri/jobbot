import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, Job, JobStats, Subscription } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      setUser: (user) => set({ user, isAuthenticated: !!user, isLoading: false }),
      logout: () => {
        localStorage.removeItem('token');
        set({ user: null, isAuthenticated: false, isLoading: false });
      },
    }),
    {
      name: 'auth-storage',
    }
  )
);

interface JobState {
  jobs: Job[];
  stats: JobStats | null;
  filters: {
    status: string | null;
    search: string;
  };
  setJobs: (jobs: Job[]) => void;
  addJob: (job: Job) => void;
  updateJob: (id: string, updates: Partial<Job>) => void;
  deleteJob: (id: string) => void;
  setStats: (stats: JobStats) => void;
  setFilters: (filters: Partial<JobState['filters']>) => void;
}

export const useJobStore = create<JobState>()(
  persist(
    (set) => ({
      jobs: [],
      stats: null,
      filters: {
        status: null,
        search: '',
      },
      setJobs: (jobs) => set({ jobs }),
      addJob: (job) => set((state) => ({ jobs: [job, ...state.jobs] })),
      updateJob: (id, updates) =>
        set((state) => ({
          jobs: state.jobs.map((j) =>
            j.id === id ? { ...j, ...updates, updatedAt: new Date().toISOString() } : j
          ),
        })),
      deleteJob: (id) =>
        set((state) => ({ jobs: state.jobs.filter((j) => j.id !== id) })),
      setStats: (stats) => set({ stats }),
      setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
    }),
    {
      name: 'job-storage',
    }
  )
);

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: 'light',
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
    }),
    {
      name: 'ui-storage',
    }
  )
);
