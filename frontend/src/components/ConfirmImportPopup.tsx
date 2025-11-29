import { useState, type FC } from 'react';
import { useI18n } from '../i18n/I18nContext';
import type { InvoiceItem, UploadResponse } from '../api/invoices';
import { X, Check, FileText, Plus, Trash2 } from 'lucide-react';

interface ConfirmImportPopupProps {
  data: UploadResponse;
  onConfirm: (data: {
    mode: 'invoice' | 'estimate';
    language: 'en' | 'fr';
    from_address: string;
    to_address: string;
    items: InvoiceItem[];
    doc_title: string;
  }) => void;
  onCancel: () => void;
}

const ConfirmImportPopup: FC<ConfirmImportPopupProps> = ({ data, onConfirm, onCancel }) => {
  const { t } = useI18n();

  // Editable state from extracted data
  const [mode, setMode] = useState<'invoice' | 'estimate'>(data.extracted.mode);
  const [language, setLanguage] = useState<'en' | 'fr'>(data.extracted.language);
  const [fromAddress, setFromAddress] = useState(data.extracted.from_address);
  const [toAddress, setToAddress] = useState(data.extracted.to_address);
  const [items, setItems] = useState<InvoiceItem[]>(data.extracted.items);
  const [docTitle, setDocTitle] = useState(data.extracted.doc_title);

  // For adding new items
  const [newDesc, setNewDesc] = useState('');
  const [newQty, setNewQty] = useState('1');
  const [newPrice, setNewPrice] = useState('');

  const currencySymbol = language === 'fr' ? '€' : '$';

  const handleConfirm = () => {
    onConfirm({
      mode,
      language,
      from_address: fromAddress,
      to_address: toAddress,
      items,
      doc_title: docTitle,
    });
  };

  const addItem = () => {
    if (!newDesc.trim()) return;
    const qty = parseInt(newQty) || 1;
    const price = parseFloat(newPrice.replace(',', '.')) || 0;

    setItems([...items, { description: newDesc.trim(), quantity: qty, price }]);
    setNewDesc('');
    setNewQty('1');
    setNewPrice('');
  };

  const removeItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const updateItem = (index: number, field: keyof InvoiceItem, value: string | number) => {
    const updated = [...items];
    if (field === 'description') {
      updated[index].description = value as string;
    } else if (field === 'quantity') {
      updated[index].quantity = parseInt(value as string) || 1;
    } else if (field === 'price') {
      updated[index].price = parseFloat((value as string).replace(',', '.')) || 0;
    }
    setItems(updated);
  };

  const total = items.reduce((sum, item) => sum + item.quantity * item.price, 0);

  const formatPrice = (value: number) => {
    return language === 'fr'
      ? value.toFixed(2).replace('.', ',')
      : value.toFixed(2);
  };

  return (
    <div className="popup-overlay" onClick={onCancel}>
      <div className="popup-modal confirm-import-popup" onClick={(e) => e.stopPropagation()}>
        <div className="popup-header">
          <h3>
            <FileText size={20} />
            {t('confirm_import_title')}
          </h3>
          <button className="btn btn-icon popup-close" onClick={onCancel}>
            <X size={20} />
          </button>
        </div>

        <div className="popup-content">
          <p className="popup-filename">{data.filename}</p>

          {/* Mode & Language */}
          <div className="confirm-row">
            <div className="confirm-field">
              <label>{t('document_type')}</label>
              <div className="mode-toggle">
                <button
                  className={`toggle-btn ${mode === 'invoice' ? 'active' : ''}`}
                  onClick={() => setMode('invoice')}
                >
                  {t('mode_invoice')}
                </button>
                <button
                  className={`toggle-btn ${mode === 'estimate' ? 'active' : ''}`}
                  onClick={() => setMode('estimate')}
                >
                  {t('mode_estimate')}
                </button>
              </div>
            </div>
            <div className="confirm-field">
              <label>{t('language')}</label>
              <div className="mode-toggle">
                <button
                  className={`toggle-btn ${language === 'fr' ? 'active' : ''}`}
                  onClick={() => setLanguage('fr')}
                >
                  FR
                </button>
                <button
                  className={`toggle-btn ${language === 'en' ? 'active' : ''}`}
                  onClick={() => setLanguage('en')}
                >
                  EN
                </button>
              </div>
            </div>
          </div>

          {/* Document Title */}
          <div className="confirm-field">
            <label>{t('doc_title_label')}</label>
            <input
              type="text"
              value={docTitle}
              onChange={(e) => setDocTitle(e.target.value)}
              placeholder={t('doc_title_placeholder')}
            />
          </div>

          {/* Addresses */}
          <div className="confirm-row">
            <div className="confirm-field">
              <label>{t('from_address_label')}</label>
              <textarea
                value={fromAddress}
                onChange={(e) => setFromAddress(e.target.value)}
                rows={3}
                placeholder={t('from_address_placeholder')}
              />
            </div>
            <div className="confirm-field">
              <label>{t('to_address_label')}</label>
              <textarea
                value={toAddress}
                onChange={(e) => setToAddress(e.target.value)}
                rows={3}
                placeholder={t('to_address_placeholder')}
              />
            </div>
          </div>

          {/* Items */}
          <div className="confirm-field">
            <label>{t('services_items')}</label>
            <div className="confirm-items">
              {items.length === 0 ? (
                <p className="no-items-text">{t('no_items_extracted')}</p>
              ) : (
                <table className="confirm-items-table">
                  <thead>
                    <tr>
                      <th>{t('description')}</th>
                      <th>{t('quantity')}</th>
                      <th>{t('unit_price')}</th>
                      <th>{t('tree_total')}</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item, index) => (
                      <tr key={index}>
                        <td>
                          <input
                            type="text"
                            value={item.description}
                            onChange={(e) => updateItem(index, 'description', e.target.value)}
                          />
                        </td>
                        <td>
                          <input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => updateItem(index, 'quantity', e.target.value)}
                            min="1"
                            style={{ width: '60px' }}
                          />
                        </td>
                        <td>
                          <input
                            type="text"
                            value={formatPrice(item.price)}
                            onChange={(e) => updateItem(index, 'price', e.target.value)}
                            style={{ width: '80px' }}
                          />
                        </td>
                        <td className="item-total">
                          {currencySymbol}{formatPrice(item.quantity * item.price)}
                        </td>
                        <td>
                          <button
                            className="btn btn-icon btn-danger-small"
                            onClick={() => removeItem(index)}
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {/* Add new item */}
              <div className="add-item-row">
                <input
                  type="text"
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  placeholder={t('description')}
                  onKeyPress={(e) => e.key === 'Enter' && addItem()}
                />
                <input
                  type="number"
                  value={newQty}
                  onChange={(e) => setNewQty(e.target.value)}
                  min="1"
                  style={{ width: '60px' }}
                />
                <input
                  type="text"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  placeholder={t('unit_price')}
                  style={{ width: '80px' }}
                  onKeyPress={(e) => e.key === 'Enter' && addItem()}
                />
                <button className="btn btn-icon btn-add-item" onClick={addItem}>
                  <Plus size={16} />
                </button>
              </div>

              {/* Total */}
              <div className="confirm-total">
                <span>{t('total_label')}</span>
                <span className="total-amount">{currencySymbol}{formatPrice(total)}</span>
              </div>
            </div>
          </div>

          {/* Raw text preview (collapsible) */}
          <details className="raw-text-details">
            <summary>{t('view_raw_text')}</summary>
            <pre className="raw-text-preview">{data.raw_text}</pre>
          </details>
        </div>

        <div className="popup-footer">
          <button className="btn btn-secondary" onClick={onCancel}>
            <X size={18} />
            {t('cancel')}
          </button>
          <button className="btn btn-success" onClick={handleConfirm}>
            <Check size={18} />
            {t('confirm_save')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmImportPopup;
