export interface User {
  id: string;
  email: string;
  name: string;
  phone?: string;
  telegramId?: string;
  preferences: UserPreferences;
  cvUrl?: string;
  createdAt: string;
  updatedAt: string;
}

export interface UserPreferences {
  searchKeywords: string[];
  location: string;
  modality: 'remote' | 'hybrid' | 'onsite' | 'any';
  notifications: NotificationPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  telegram: boolean;
  browser: boolean;
  newJobs: boolean;
  interviewReminders: boolean;
  weeklyDigest: boolean;
}

export type JobStatus = 'applied' | 'interview' | 'offer' | 'rejected' | 'saved';

export interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  modality: 'remote' | 'hybrid' | 'onsite';
  description?: string;
  salary?: string;
  url: string;
  status: JobStatus;
  appliedAt?: string;
  notes?: string;
  createdAt: string;
  updatedAt: string;
}

export interface JobStats {
  totalApplied: number;
  totalInterviews: number;
  totalOffers: number;
  totalRejected: number;
  responseRate: number;
  weeklyChange: number;
}

export interface Subscription {
  id: string;
  plan: 'free' | 'premium';
  status: 'active' | 'cancelled' | 'past_due';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  cancelAtPeriodEnd: boolean;
}

export interface Invoice {
  id: string;
  amount: number;
  currency: string;
  status: 'paid' | 'open' | 'void';
  createdAt: string;
  pdfUrl?: string;
}

export interface ApiError {
  message: string;
  code: string;
  statusCode: number;
}
