import React, { useState } from 'react';
import { Scroll, ChevronDown, BookMarked } from 'lucide-react';
import { HistoricalTrivia } from '../../types/lesson';
import { Badge } from '../ui/Badge';

interface HistoricalTriviaCardProps {
  trivia: HistoricalTrivia;
  className?: string;
}

export const HistoricalTriviaCard: React.FC<HistoricalTriviaCardProps> = ({
  trivia,
  className = '',
}) => {
  // 1. Initial state must be closed by default
  const [isExpanded, setIsExpanded] = useState<boolean>(false);

  // 2. Safe extraction of trivia body text (fact, content, or text)
  const triviaBody =
    trivia.fact || trivia.content || (trivia as Record<string, any>).text || '';

  // 3. Safe extraction of badge tag (period, century, or Latin motto)
  const tagBadge =
    trivia.century_or_period ||
    (trivia.latin_motto_or_phrase ? 'Latinitas' : 'Antiquitas');

  return (
    <div
      className={`rounded-2xl border-2 border-amber-400/80 bg-gradient-to-br from-[#fcfbf9] via-[#fdf6e7]/40 to-amber-50/50 p-5 shadow-md relative overflow-hidden transition-all duration-300 ${className}`}
    >
      {/* Decorative Golden Corner & Watermark */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
      <div className="absolute -bottom-4 -right-2 text-stone-300/20 font-serif text-8xl select-none pointer-events-none">
        🏛️
      </div>

      {/* Header with Wax Seal Motif and Expand Toggle */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between cursor-pointer select-none group"
      >
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-600 to-amber-400 text-white flex items-center justify-center shadow-md shadow-amber-800/20 flex-shrink-0">
            <Scroll className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-[10px] font-serif font-bold uppercase tracking-widest text-amber-800">
                • VOCÊ SABIA? • HISTORIA ANTIQUA
              </span>
              {tagBadge && (
                <Badge variant="warning" size="sm">
                  {tagBadge}
                </Badge>
              )}
            </div>
            <h4 className="font-serif font-bold text-stone-900 text-base group-hover:text-amber-900 transition-colors">
              {trivia.title}
            </h4>
          </div>
        </div>

        {/* Chevron icon: visible at all times, rotates 180° when expanded */}
        <div
          className="p-2 rounded-xl text-stone-600 group-hover:text-amber-900 group-hover:bg-amber-100/60 transition-colors flex-shrink-0 ml-2"
          title={isExpanded ? 'Recolher curiosidade' : 'Expandir curiosidade'}
        >
          <ChevronDown
            className={`w-5 h-5 text-amber-800 transition-transform duration-300 ease-in-out ${
              isExpanded ? 'rotate-180' : 'rotate-0'
            }`}
          />
        </div>
      </div>

      {/* Expandable Content Body */}
      {isExpanded && (
        <div className="mt-3.5 pt-3.5 border-t border-amber-200/70 space-y-2.5 animate-fadeIn">
          {/* Main Trivia Body Text rendered above canonical source */}
          {triviaBody && (
            <p className="text-xs sm:text-sm text-stone-800 leading-relaxed font-sans">
              {triviaBody}
            </p>
          )}

          {/* Latin Motto if available */}
          {trivia.latin_motto_or_phrase && (
            <div className="p-2.5 rounded-lg bg-amber-100/60 border border-amber-200/70 text-xs font-serif italic text-amber-950">
              « {trivia.latin_motto_or_phrase} »
            </div>
          )}

          {/* Canonical Source Reference */}
          {trivia.source_reference && (
            <div className="flex items-center gap-1.5 pt-1 text-[11px] text-amber-900/80 font-serif italic">
              <BookMarked className="w-3.5 h-3.5 flex-shrink-0 text-amber-700" />
              <span>Fonte Canônica: {trivia.source_reference}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

