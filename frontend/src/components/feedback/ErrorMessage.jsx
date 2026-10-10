import React from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';
import { cn } from '../../utils/cn';

/**
 * Inline or panel error feedback component with optional retry callback.
 */
export function ErrorMessage({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
}) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-red-950/20 border border-red-800/40 text-red-200',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 mt-0.5 shrink-0" aria-hidden="true" />
        <div>
          <h4 className="text-sm font-semibold text-red-100">{title}</h4>
          {message && <p className="text-xs text-red-300/90 mt-0.5 leading-relaxed">{message}</p>}
        </div>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium bg-red-900/40 hover:bg-red-800/50 text-red-100 border border-red-700/50 transition-colors focus-ring"
        >
          <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}
