import React from 'react';
import { cn } from '../../utils/cn';

/**
 * SafeMarkdown — Safely formats plain text / simple Markdown without allowing any raw HTML or XSS injection.
 * Escapes HTML characters before parsing inline styles (*italic*, **bold**, `code`, > quote, lists).
 */
export function SafeMarkdown({ content = '', className }) {
  if (!content) return null;

  // 1. Clean string
  const text = String(content);

  // 2. Split into blocks by double newlines
  const blocks = text.split(/\n\s*\n/);

  const renderInline = (str) => {
    // Regex for bold, italic, inline code
    // Escape angle brackets to prevent any HTML injection
    const parts = [];
    let remaining = str;
    let keyIdx = 0;

    // Tokenize bold, italic, code
    const regex = /(\*\*[^*]+\*\*|__[^_]+__|\*[^*]+\*|_[^_]+_|`[^`]+`)/g;
    let match;
    let lastIndex = 0;

    while ((match = regex.exec(remaining)) !== null) {
      if (match.index > lastIndex) {
        parts.push(remaining.substring(lastIndex, match.index));
      }
      const token = match[0];
      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={`b-${keyIdx++}`} className="font-semibold text-text-primary">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('__') && token.endsWith('__')) {
        parts.push(
          <strong key={`b-${keyIdx++}`} className="font-semibold text-text-primary">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('*') && token.endsWith('*')) {
        parts.push(
          <em key={`i-${keyIdx++}`} className="italic text-text-primary/90">
            {token.slice(1, -1)}
          </em>
        );
      } else if (token.startsWith('_') && token.endsWith('_')) {
        parts.push(
          <em key={`i-${keyIdx++}`} className="italic text-text-primary/90">
            {token.slice(1, -1)}
          </em>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code
            key={`c-${keyIdx++}`}
            className="px-1.5 py-0.5 rounded bg-surface-2 text-teal text-xs font-mono border border-border-neutral"
          >
            {token.slice(1, -1)}
          </code>
        );
      }
      lastIndex = match.index + token.length;
    }

    if (lastIndex < remaining.length) {
      parts.push(remaining.substring(lastIndex));
    }

    return parts;
  };

  return (
    <div className={cn('space-y-2.5 text-sm leading-relaxed text-text-secondary', className)}>
      {blocks.map((block, idx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // Blockquote
        if (trimmed.startsWith('>')) {
          const quoteText = trimmed.replace(/^>\s*/, '');
          return (
            <blockquote
              key={`b-${idx}`}
              className="border-l-2 border-teal pl-3 py-0.5 italic text-text-secondary bg-surface-2/30 rounded-r"
            >
              {renderInline(quoteText)}
            </blockquote>
          );
        }

        // Bullet list
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const items = trimmed.split('\n').filter((l) => l.trim().startsWith('- ') || l.trim().startsWith('* '));
          return (
            <ul key={`ul-${idx}`} className="list-disc list-inside space-y-1 pl-1">
              {items.map((item, itemIdx) => (
                <li key={`li-${itemIdx}`}>
                  {renderInline(item.replace(/^[-*]\s+/, ''))}
                </li>
              ))}
            </ul>
          );
        }

        // Standard Paragraph with soft linebreaks preserved
        const lines = trimmed.split('\n');
        return (
          <p key={`p-${idx}`}>
            {lines.map((line, lineIdx) => (
              <React.Fragment key={`l-${lineIdx}`}>
                {renderInline(line)}
                {lineIdx < lines.length - 1 && <br />}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
}
