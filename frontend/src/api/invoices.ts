import axios from 'axios';
import { supabase } from '../lib/supabase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests (with timeout to prevent hanging)
api.interceptors.request.use(async (config) => {
  try {
    // Add timeout to prevent infinite waiting
    const sessionPromise = supabase.auth.getSession();
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('Session timeout')), 5000)
    );

    const { data: { session } } = await Promise.race([sessionPromise, timeoutPromise]) as { data: { session: { access_token: string } | null } };
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  } catch (err) {
    console.warn('Failed to get auth session:', err);
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

export interface InvoiceItem {
  description: string;
  quantity: number;
  price: number;
}

export interface InvoiceCreate {
  from_address: string;
  to_address: string;
  items: InvoiceItem[];
  mode: 'invoice' | 'estimate';
  language: 'en' | 'fr';
  doc_title?: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  date: string;
  from_address: string;
  to_address: string;
  items: InvoiceItem[];
  mode: string;
  language: string;
  total: number;
  created_at: string;
  doc_title?: string;
}

export interface UploadResponse {
  success: boolean;
  filename: string;
  file_id: string;
  saved_path: string;
  extracted: {
    mode: 'invoice' | 'estimate';
    language: 'en' | 'fr';
    from_address: string;
    to_address: string;
    items: InvoiceItem[];
    total: number;
    doc_title: string;
  };
  raw_text: string;
}

export const invoiceApi = {
  // Create a new invoice
  create: async (invoice: InvoiceCreate): Promise<Invoice> => {
    const response = await api.post('/invoices/', invoice);
    return response.data;
  },

  // Get all invoices
  list: async (): Promise<Invoice[]> => {
    const response = await api.get('/invoices/');
    return response.data;
  },

  // Get a single invoice
  get: async (id: string): Promise<Invoice> => {
    const response = await api.get(`/invoices/${id}`);
    return response.data;
  },

  // Delete an invoice
  delete: async (id: string): Promise<void> => {
    await api.delete(`/invoices/${id}`);
  },

  // Download PDF for an invoice
  downloadPdf: async (id: string): Promise<Blob> => {
    const response = await api.get(`/invoices/${id}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Generate PDF without saving (preview)
  generatePdf: async (invoice: InvoiceCreate): Promise<Blob> => {
    const response = await api.post('/invoices/generate-pdf', invoice, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Upload PDF and extract data
  uploadPdf: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/invoices/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000, // 30 second timeout for PDF processing
    });
    return response.data;
  },
};

export default api;
