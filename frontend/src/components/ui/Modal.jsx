import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Accessible Modal dialog component.
 */
export function Modal({
  isOpen,
  onClose,
  title,
  children,
  maxWidth = 'max-w-md',
  className,
}) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-background-deep/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Surface */}
      <div
        className={cn(
          'relative w-full rounded-2xl bg-surface-1 border border-border-neutral p-6 shadow-2xl z-10 transition-all overflow-hidden',
          maxWidth,
          className
        )}
      >
        <div className="flex items-center justify-between pb-4 border-b border-border-neutral/60 mb-4">
          <h2 id="modal-title" className="text-lg font-bold text-text-primary tracking-tight">
            {title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-2 transition-colors focus-ring"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="text-text-primary">{children}</div>
      </div>
    </div>
  );
}
