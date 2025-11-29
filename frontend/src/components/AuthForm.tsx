import { useState, type FC, type FormEvent } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useI18n } from '../i18n/I18nContext';
import { LogIn, UserPlus, Mail, Lock, User } from 'lucide-react';

interface AuthFormProps {
  onSuccess?: () => void;
}

const AuthForm: FC<AuthFormProps> = ({ onSuccess }) => {
  const { t } = useI18n();
  const { signIn, signUp } = useAuth();
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      if (mode === 'signin') {
        const { error } = await signIn(email, password);
        if (error) {
          setError(error.message);
        } else {
          onSuccess?.();
        }
      } else {
        const { error } = await signUp(email, password, fullName);
        if (error) {
          setError(error.message);
        } else {
          setMessage(t('signup_success'));
          setMode('signin');
        }
      }
    } catch (err) {
      setError(t('auth_error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-form-container">
      <div className="auth-form">
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'signin' ? 'active' : ''}`}
            onClick={() => setMode('signin')}
            type="button"
          >
            <LogIn size={18} />
            {t('signin')}
          </button>
          <button
            className={`auth-tab ${mode === 'signup' ? 'active' : ''}`}
            onClick={() => setMode('signup')}
            type="button"
          >
            <UserPlus size={18} />
            {t('signup')}
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {error && <div className="auth-error">{error}</div>}
          {message && <div className="auth-message">{message}</div>}

          {mode === 'signup' && (
            <div className="form-group">
              <label>
                <User size={16} />
                {t('full_name')}
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder={t('full_name_placeholder')}
              />
            </div>
          )}

          <div className="form-group">
            <label>
              <Mail size={16} />
              {t('email')}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('email_placeholder')}
              required
            />
          </div>

          <div className="form-group">
            <label>
              <Lock size={16} />
              {t('password')}
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('password_placeholder')}
              required
              minLength={6}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary auth-submit"
            disabled={loading}
          >
            {loading ? '...' : mode === 'signin' ? t('signin') : t('signup')}
          </button>
        </form>

        <p className="auth-switch">
          {mode === 'signin' ? t('no_account') : t('have_account')}
          <button
            type="button"
            className="link-btn"
            onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')}
          >
            {mode === 'signin' ? t('signup') : t('signin')}
          </button>
        </p>
      </div>
    </div>
  );
};

export default AuthForm;
