import React, { useState } from 'react';
import { LogIn } from 'lucide-react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { ErrorMessage } from '../feedback/ErrorMessage';
import { useAuth } from '../../hooks/useAuth';

/**
 * AuthModal — Session login modal connecting to Django Session Auth.
 */
export function AuthModal({ isOpen, onClose }) {
  const { login, loading, authError } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);

    if (!username.trim() || !password) {
      setFormError('Please enter both username and password.');
      return;
    }

    const result = await login(username.trim(), password);
    if (result.success) {
      setUsername('');
      setPassword('');
      onClose();
    } else {
      setFormError(result.error);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Sign In to DreamTeal">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {(formError || authError) && (
          <ErrorMessage
            title="Authentication Error"
            message={formError || authError}
          />
        )}

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="auth-username"
            className="text-xs font-medium text-text-secondary uppercase tracking-wider"
          >
            Username
          </label>
          <input
            id="auth-username"
            type="text"
            required
            autoComplete="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="e.g. dreamteal_tester"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary placeholder:text-text-muted focus-ring text-sm"
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label
            htmlFor="auth-password"
            className="text-xs font-medium text-text-secondary uppercase tracking-wider"
          >
            Password
          </label>
          <input
            id="auth-password"
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3.5 py-2.5 rounded-lg bg-surface-2 border border-border-neutral text-text-primary placeholder:text-text-muted focus-ring text-sm"
          />
        </div>

        <div className="pt-2">
          <Button
            type="submit"
            variant="primary"
            loading={loading}
            icon={LogIn}
            className="w-full py-2.5"
          >
            Sign In with Session
          </Button>
        </div>

        <p className="text-center text-xs text-text-muted mt-2">
          Session Authentication backed by secure HTTP-only cookie and CSRF protection.
        </p>
      </form>
    </Modal>
  );
}
