import type { FC } from 'react';
import { useI18n } from '../i18n/I18nContext';
import { Languages } from 'lucide-react';

const LanguageSelector: FC = () => {
  const { language, setLanguage, t } = useI18n();

  return (
    <div className="language-selector">
      <Languages size={20} />
      <button
        className={`lang-btn ${language === 'en' ? 'active' : ''}`}
        onClick={() => setLanguage('en')}
      >
        {t('lang_en')}
      </button>
      <button
        className={`lang-btn ${language === 'fr' ? 'active' : ''}`}
        onClick={() => setLanguage('fr')}
      >
        {t('lang_fr')}
      </button>
    </div>
  );
};

export default LanguageSelector;
