import { useEffect, useState, type FC } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { useAuth } from '../contexts/AuthContext';
import { invoiceApi } from '../api/invoices';
import type { Invoice } from '../api/invoices';
import { Download, Trash2, FileText } from 'lucide-react';

const InvoiceHistory: FC = () => {
  const { t, language } = useI18n();
  const { user, loading: authLoading } = useAuth();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const currencySymbol = language === 'fr' ? '€' : '$';

  const fetchInvoices = async () => {
    if (!user) {
      setInvoices([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError('');
      const data = await invoiceApi.list();
      setInvoices(data);
    } catch (err: unknown) {
      const errorObj = err as { response?: { status?: number } };
      if (errorObj?.response?.status === 401) {
        setError(t('auth_required'));
      } else {
        setError(t('history_load_error'));
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authLoading) {
      fetchInvoices();
    }
  }, [user, authLoading]);

  const handleDownload = async (invoice: Invoice) => {
    try {
      const blob = await invoiceApi.downloadPdf(invoice.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${invoice.mode}_${invoice.invoice_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to download PDF:', err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t('delete_confirm'))) return;

    try {
      await invoiceApi.delete(id);
      setInvoices(invoices.filter(inv => inv.id !== id));
    } catch (err) {
      console.error('Failed to delete invoice:', err);
      setError(t('delete_fail'));
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString(language === 'fr' ? 'fr-FR' : 'en-US');
  };

  const formatPrice = (value: number) => {
    return language === 'fr'
      ? value.toFixed(2).replace('.', ',')
      : value.toFixed(2);
  };

  if (loading || authLoading) {
    return <div className="loading">{t('loading')}</div>;
  }

  if (!user) {
    return (
      <div className="invoice-history">
        <h2><FileText size={24} /> {t('history')}</h2>
        <p className="no-invoices">{t('login_to_see_history')}</p>
      </div>
    );
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="invoice-history">
      <h2><FileText size={24} /> {t('history')}</h2>

      {invoices.length === 0 ? (
        <p className="no-invoices">{t('no_invoices')}</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Date</th>
              <th>Type</th>
              <th>To</th>
              <th>Total</th>
              <th>{t('actions')}</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((invoice) => (
              <tr key={invoice.id}>
                <td>{invoice.invoice_number}</td>
                <td>{formatDate(invoice.date)}</td>
                <td>
                  <span className={`badge badge-${invoice.mode}`}>
                    {invoice.mode === 'invoice'
                      ? t('mode_invoice')
                      : t('mode_estimate')}
                  </span>
                </td>
                <td className="to-address">
                  {invoice.to_address.split('\n')[0]}
                </td>
                <td className="total">
                  {currencySymbol}{formatPrice(invoice.total)}
                </td>
                <td className="actions">
                  <button
                    className="btn btn-icon btn-primary"
                    onClick={() => handleDownload(invoice)}
                    title={t('download')}
                  >
                    <Download size={16} />
                  </button>
                  <button
                    className="btn btn-icon btn-danger"
                    onClick={() => handleDelete(invoice.id)}
                    title={t('delete')}
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default InvoiceHistory;
