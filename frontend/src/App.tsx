import { useState } from 'react';
import { I18nProvider } from './i18n/I18nContext';
import { useI18n } from './i18n/I18nContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LanguageSelector from './components/LanguageSelector';
import InvoiceForm from './components/InvoiceForm';
import InvoiceHistory from './components/InvoiceHistory';
import AuthForm from './components/AuthForm';
import { invoiceApi } from './api/invoices';
import type { InvoiceItem, InvoiceCreate } from './api/invoices';
import { FileText, History, LogOut, User } from 'lucide-react';
import './App.css';

const DEFAULT_FROM_ADDRESS = `Wael
9 rue Olympe de Gouges,
92600 Asnières-sur-Seine, France`;

function InvoiceApp() {
  const { t, language } = useI18n();
  const { user, signOut, loading: authLoading } = useAuth();
  const [items, setItems] = useState<InvoiceItem[]>([]);
  const [mode, setMode] = useState<'invoice' | 'estimate'>('invoice');
  const [fromAddress, setFromAddress] = useState(DEFAULT_FROM_ADDRESS);
  const [toAddress, setToAddress] = useState('');
  const [docTitle, setDocTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 3000);
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="app">
        <div className="loading-container">
          <div className="loading">Loading...</div>
        </div>
      </div>
    );
  }

  // Show auth form if not logged in
  if (!user) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>
            <img src="/logo.png" alt="Logo" className="header-logo" />
            {t('title')}
          </h1>
          <LanguageSelector />
        </header>
        <AuthForm />
      </div>
    );
  }

  const getInvoiceData = (): InvoiceCreate => ({
    from_address: fromAddress,
    to_address: toAddress,
    items,
    mode,
    language,
    doc_title: docTitle || undefined,
  });

  const handleGenerate = async () => {
    if (items.length === 0) {
      showMessage('error', t('no_items'));
      return;
    }

    try {
      setLoading(true);
      const blob = await invoiceApi.generatePdf(getInvoiceData());

      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Generate filename
      const dateStr = new Date().toISOString().slice(2, 10).replace(/-/g, '');
      const safeTitle = docTitle
        ? docTitle.replace(/[^a-zA-Z0-9\s-_]/g, '').replace(/\s+/g, '_')
        : mode;
      link.download = `${safeTitle}_${dateStr}.pdf`;

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      showMessage('success', t('generate_success'));
    } catch (err) {
      showMessage('error', t('generate_fail'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (items.length === 0) {
      showMessage('error', t('no_items'));
      return;
    }

    try {
      setLoading(true);
      await invoiceApi.create(getInvoiceData());
      showMessage('success', t('generate_success'));
      handleClear();
      setActiveTab('history');
    } catch (err) {
      showMessage('error', t('generate_fail'));
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setItems([]);
    setToAddress('');
    setDocTitle('');
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>
          <img src="/logo.png" alt="Logo" className="header-logo" />
          {t('title')}
        </h1>
        <div className="header-actions">
          <div className="user-info">
            <User size={18} />
            <span>{user.email}</span>
            <button className="btn btn-icon" onClick={signOut} title={t('signout')}>
              <LogOut size={18} />
            </button>
          </div>
          <LanguageSelector />
        </div>
      </header>

      {message && (
        <div className={`message message-${message.type}`}>
          {message.text}
        </div>
      )}

      <nav className="tabs">
        <button
          className={`tab ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => setActiveTab('create')}
        >
          <FileText size={18} />
          {t('mode_invoice')} / {t('mode_estimate')}
        </button>
        <button
          className={`tab ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <History size={18} />
          {t('history')}
        </button>
      </nav>

      <main className="main-content">
        {activeTab === 'create' ? (
          <InvoiceForm
            items={items}
            setItems={setItems}
            mode={mode}
            setMode={setMode}
            fromAddress={fromAddress}
            setFromAddress={setFromAddress}
            toAddress={toAddress}
            setToAddress={setToAddress}
            docTitle={docTitle}
            setDocTitle={setDocTitle}
            onGenerate={handleGenerate}
            onSave={handleSave}
            onClear={handleClear}
            loading={loading}
            showMessage={showMessage}
          />
        ) : (
          <InvoiceHistory />
        )}
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <I18nProvider>
        <InvoiceApp />
      </I18nProvider>
    </AuthProvider>
  );
}

export default App;
