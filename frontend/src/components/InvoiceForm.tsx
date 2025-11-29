import { useState, useRef, type FC, type Dispatch, type SetStateAction } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { invoiceApi } from '../api/invoices';
import type { InvoiceItem, UploadResponse } from '../api/invoices';
import { Plus, Trash2, Upload } from 'lucide-react';
import ConfirmImportPopup from './ConfirmImportPopup';

interface InvoiceFormProps {
  items: InvoiceItem[];
  setItems: Dispatch<SetStateAction<InvoiceItem[]>>;
  mode: 'invoice' | 'estimate';
  setMode: Dispatch<SetStateAction<'invoice' | 'estimate'>>;
  fromAddress: string;
  setFromAddress: Dispatch<SetStateAction<string>>;
  toAddress: string;
  setToAddress: Dispatch<SetStateAction<string>>;
  docTitle: string;
  setDocTitle: Dispatch<SetStateAction<string>>;
  onGenerate: () => void;
  onSave: () => void;
  onClear: () => void;
  loading: boolean;
  showMessage: (type: 'success' | 'error', text: string) => void;
}

const DEFAULT_FROM_ADDRESS = `Wael
9 rue Olympe de Gouges,
92600 Asnières-sur-Seine, France`;

const InvoiceForm: FC<InvoiceFormProps> = ({
  items,
  setItems,
  mode,
  setMode,
  fromAddress,
  setFromAddress,
  toAddress,
  setToAddress,
  docTitle,
  setDocTitle,
  onGenerate,
  onSave,
  onClear,
  loading,
  showMessage,
}) => {
  const { t, language, setLanguage } = useI18n();
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [price, setPrice] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const currencySymbol = language === 'fr' ? '€' : '$';

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      const result = await invoiceApi.uploadPdf(file);

      if (result.success) {
        // Show confirmation popup with extracted data
        setUploadData(result);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      showMessage('error', t('upload_fail'));
    } finally {
      setUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleConfirmImport = async (data: {
    mode: 'invoice' | 'estimate';
    language: 'en' | 'fr';
    from_address: string;
    to_address: string;
    items: InvoiceItem[];
    doc_title: string;
  }) => {
    // Apply the confirmed data to the form
    setMode(data.mode);
    setLanguage(data.language);
    setFromAddress(data.from_address || DEFAULT_FROM_ADDRESS);
    setToAddress(data.to_address);
    setItems(data.items);
    setDocTitle(data.doc_title);

    // Close popup
    setUploadData(null);
    showMessage('success', t('import_success'));
  };

  const handleCancelImport = () => {
    setUploadData(null);
  };

  const addItem = () => {
    setError('');

    if (!description.trim()) {
      setError(t('error_desc_empty'));
      return;
    }

    const qty = parseInt(quantity);
    if (isNaN(qty) || qty <= 0) {
      setError(t('error_qty_invalid'));
      return;
    }

    const priceVal = parseFloat(price.replace(',', '.'));
    if (isNaN(priceVal) || priceVal < 0) {
      setError(t('error_price_invalid'));
      return;
    }

    setItems([...items, { description: description.trim(), quantity: qty, price: priceVal }]);
    setDescription('');
    setQuantity('1');
    setPrice('');
  };

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const total = items.reduce((sum, item) => sum + item.quantity * item.price, 0);

  const formatPrice = (value: number) => {
    return language === 'fr'
      ? value.toFixed(2).replace('.', ',')
      : value.toFixed(2);
  };

  return (
    <div className="invoice-form">
      {/* Confirmation Popup for PDF Import */}
      {uploadData && (
        <ConfirmImportPopup
          data={uploadData}
          onConfirm={handleConfirmImport}
          onCancel={handleCancelImport}
        />
      )}

      {/* Upload Section */}
      <div className="upload-section">
        <input
          type="file"
          ref={fileInputRef}
          accept=".pdf"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          id="pdf-upload"
        />
        <button
          className="btn btn-outline upload-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading || loading}
        >
          <Upload size={20} />
          {uploading ? t('uploading') : t('import_pdf')}
        </button>
        <span className="upload-hint">{t('import_hint')}</span>
      </div>

      <div className="separator">
        <span>{t('or_manual_entry')}</span>
      </div>

      {/* Mode Selection */}
      <div className="mode-selector">
        <label className="mode-option">
          <input
            type="radio"
            value="invoice"
            checked={mode === 'invoice'}
            onChange={() => setMode('invoice')}
          />
          {t('mode_invoice')}
        </label>
        <label className="mode-option">
          <input
            type="radio"
            value="estimate"
            checked={mode === 'estimate'}
            onChange={() => setMode('estimate')}
          />
          {t('mode_estimate')}
        </label>
      </div>

      {/* Address Section */}
      <div className="section addresses-section">
        <h3>{t('addresses_section')}</h3>

        <div className="form-group">
          <label>{t('doc_title_label')}</label>
          <input
            type="text"
            value={docTitle}
            onChange={(e) => setDocTitle(e.target.value)}
            placeholder={t('doc_title_placeholder')}
            className="input-full"
          />
        </div>

        <div className="address-grid">
          <div className="form-group">
            <label>{t('from_address_label')}</label>
            <textarea
              value={fromAddress || DEFAULT_FROM_ADDRESS}
              onChange={(e) => setFromAddress(e.target.value)}
              rows={3}
            />
          </div>
          <div className="form-group">
            <label>{t('to_address_label')}</label>
            <textarea
              value={toAddress}
              onChange={(e) => setToAddress(e.target.value)}
              rows={3}
              placeholder="Customer Name&#10;Address Line 1&#10;City, Country"
            />
          </div>
        </div>
      </div>

      {/* Add Item Section */}
      <div className="section add-item-section">
        <h3>{t('add_item')}</h3>

        {error && <div className="error-message">{error}</div>}

        <div className="add-item-grid">
          <div className="form-group">
            <label>{t('description')}</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addItem()}
            />
          </div>
          <div className="form-group">
            <label>{t('quantity')}</label>
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              min="1"
            />
          </div>
          <div className="form-group">
            <label>{t('unit_price')}</label>
            <input
              type="text"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && addItem()}
            />
          </div>
          <button className="btn btn-primary add-btn" onClick={addItem}>
            <Plus size={20} />
            {t('add_button')}
          </button>
        </div>
      </div>

      {/* Items List */}
      <div className="section items-section">
        <h3>{t('invoice_items')}</h3>

        {items.length === 0 ? (
          <p className="no-items">{t('no_items')}</p>
        ) : (
          <table className="items-table">
            <thead>
              <tr>
                <th>{t('tree_desc')}</th>
                <th>{t('tree_qty')}</th>
                <th>{t('tree_price')}</th>
                <th>{t('tree_total')}</th>
                <th>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, index) => (
                <tr key={index}>
                  <td>{item.description}</td>
                  <td>{item.quantity}</td>
                  <td>{formatPrice(item.price)}</td>
                  <td>{formatPrice(item.quantity * item.price)}</td>
                  <td>
                    <button
                      className="btn btn-icon btn-danger"
                      onClick={() => removeItem(index)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <div className="total-row">
          <span className="total-label">{t('total_label')}</span>
          <span className="total-value">
            {currencySymbol}{formatPrice(total)}
          </span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="action-buttons">
        <button
          className="btn btn-primary"
          onClick={onGenerate}
          disabled={items.length === 0 || loading}
        >
          {t('preview')}
        </button>
        <button
          className="btn btn-success"
          onClick={onSave}
          disabled={items.length === 0 || loading}
        >
          {t('save_button')}
        </button>
        <button
          className="btn btn-secondary"
          onClick={onClear}
          disabled={loading}
        >
          {t('clear_button')}
        </button>
      </div>
    </div>
  );
};

export default InvoiceForm;
