import React from 'react';
import { Bot, Sparkles } from 'lucide-react';

interface FloatingMagisterButtonProps {
  onClick: () => void;
  isOpen: boolean;
  hasUnread?: boolean;
}

export const FloatingMagisterButton: React.FC<FloatingMagisterButtonProps> = ({
  onClick,
  isOpen,
  hasUnread = false,
}) => {
  if (isOpen) return null;

  return (
    <button
      type="button"
      onClick={onClick}
      className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 text-white shadow-xl shadow-amber-950/25 border-2 border-amber-400/80 hover:scale-105 active:scale-95 transition-all cursor-pointer group"
      title="Abrir Chat Interativo com o Magister Latium"
    >
      <div className="relative">
        <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 group-hover:rotate-12 transition-transform">
          <Bot className="w-5 h-5" />
        </div>
        {hasUnread && (
          <span className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full border-2 border-stone-900 animate-pulse" />
        )}
      </div>
      <div className="text-left hidden sm:block">
        <span className="block text-[9px] font-serif font-bold uppercase tracking-widest text-amber-400">
          • Magister AI •
        </span>
        <span className="block text-xs font-serif font-semibold text-stone-100">
          Tire Dúvidas
        </span>
      </div>
      <Sparkles className="w-4 h-4 text-amber-300 animate-pulse ml-0.5" />
    </button>
  );
};
