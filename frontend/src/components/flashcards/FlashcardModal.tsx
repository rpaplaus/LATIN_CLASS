import React, { useState, useEffect, useCallback } from 'react';
import {
  X,
  ChevronLeft,
  ChevronRight,
  RotateCw,
  Sparkles,
  BookOpen,
} from 'lucide-react';
import { FlashcardItem } from '../../types/flashcard';
import { LatinAudioButton } from '../common/LatinAudioButton';

interface FlashcardModalProps {
  isOpen: boolean;
  onClose: () => void;
  flashcards: FlashcardItem[];
  lessonTitle: string;
}

export const FlashcardModal: React.FC<FlashcardModalProps> = ({
  isOpen,
  onClose,
  flashcards,
  lessonTitle,
}) => {
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [isFlipped, setIsFlipped] = useState<boolean>(false);

  const total = flashcards.length;
  const currentCard: FlashcardItem | undefined = flashcards[currentIndex];

  const handleNext = useCallback(() => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev + 1 < total ? prev + 1 : 0));
  }, [total]);

  const handlePrev = useCallback(() => {
    setIsFlipped(false);
    setCurrentIndex((prev) => (prev - 1 >= 0 ? prev - 1 : total - 1));
  }, [total]);

  const handleFlip = () => {
    setIsFlipped((prev) => !prev);
  };

  // Keyboard navigation: ArrowLeft, ArrowRight, Space (flip), Escape (close)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handlePrev();
      } else if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        handleFlip();
      } else if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleNext, handlePrev, onClose]);

  // Reset state when opening
  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(0);
      setIsFlipped(false);
    }
  }, [isOpen]);

  if (!isOpen || !currentCard) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg flex flex-col items-center">
        {/* Top Header Bar */}
        <div className="w-full flex items-center justify-between mb-4 text-stone-300">
          <div className="flex items-center space-x-2">
            <Sparkles className="text-amber-400" size={18} />
            <span className="text-xs uppercase tracking-widest text-amber-300/90 font-serif font-bold truncate max-w-[280px]">
              {lessonTitle} • {currentIndex + 1} de {total}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full bg-stone-800/80 hover:bg-stone-700 text-stone-400 hover:text-white transition-colors"
            aria-label="Fechar Flashcards"
          >
            <X size={20} />
          </button>
        </div>

        {/* 3D Flip Card Container */}
        <div
          onClick={handleFlip}
          className="w-full h-[460px] cursor-pointer select-none [perspective:1200px]"
        >
          <div
            className={`relative w-full h-full duration-500 rounded-2xl shadow-2xl transition-transform [transform-style:preserve-3d] ${
              isFlipped ? '[transform:rotateY(180deg)]' : ''
            }`}
          >
            {/* FRONT FACE */}
            <div className="absolute inset-0 w-full h-full rounded-2xl bg-gradient-to-b from-stone-900 via-stone-900/95 to-amber-950/40 border-2 border-amber-500/40 p-6 flex flex-col justify-between [backface-visibility:hidden] shadow-xl shadow-amber-950/20">
              {/* Card Header & Artwork */}
              <div className="flex flex-col items-center">
                <div className="w-full h-48 rounded-xl overflow-hidden bg-stone-950 border border-amber-500/20 mb-4 flex items-center justify-center shadow-inner">
                  {currentCard.image_url ? (
                    <img
                      src={currentCard.image_url}
                      alt={currentCard.word}
                      className="w-full h-full object-cover object-center transition-transform hover:scale-105 duration-300"
                    />
                  ) : (
                    <div className="flex flex-col items-center text-amber-400/60 p-4">
                      <BookOpen size={48} className="mb-2" />
                      <span className="text-xs font-serif tracking-wider">PICTOR LATIUM</span>
                    </div>
                  )}
                </div>

                {/* Latin Word with Pronunciation */}
                <div className="flex items-center space-x-3 mb-1">
                  <h3 className="text-3xl font-serif font-bold text-amber-300 tracking-wide">
                    {currentCard.word}
                  </h3>
                  <LatinAudioButton
                    text={currentCard.word}
                    audioUrl={currentCard.audio_url}
                    audioBase64={currentCard.audio_base64}
                    size="sm"
                  />
                </div>

                <p className="text-sm font-serif italic text-stone-400 text-center">
                  {currentCard.dictionary_entry}
                </p>
              </div>

              {/* Bottom hint */}
              <div className="pt-4 border-t border-stone-800/80 flex items-center justify-center text-xs text-stone-500 space-x-1.5">
                <RotateCw size={14} className="text-amber-400/80 animate-spin-slow" />
                <span>Clique no cartão ou pressione espaço para virar</span>
              </div>
            </div>

            {/* BACK FACE */}
            <div className="absolute inset-0 w-full h-full rounded-2xl bg-gradient-to-b from-stone-900 via-amber-950/30 to-stone-950 border-2 border-amber-400/60 p-6 flex flex-col justify-between [transform:rotateY(180deg)] [backface-visibility:hidden] shadow-xl">
              <div>
                <div className="text-center mb-4">
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 uppercase tracking-widest">
                    Tradução & Gramática
                  </span>
                </div>

                {/* Translation Headline */}
                <div className="text-center my-4 p-4 rounded-xl bg-stone-950/60 border border-stone-800">
                  <p className="text-2xl font-bold text-amber-200">
                    "{currentCard.translation}"
                  </p>
                  <p className="text-xs text-stone-400 mt-1 font-medium">
                    {currentCard.grammatical_class}
                  </p>
                </div>

                {/* Example Sentence with Audio */}
                <div className="p-4 rounded-xl bg-stone-900/80 border border-amber-900/40">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-serif font-bold text-amber-400/90 uppercase tracking-wider">
                      Exemplo Clássico:
                    </span>
                    <LatinAudioButton
                      text={currentCard.example_sentence}
                      size="sm"
                    />
                  </div>
                  <p className="text-sm font-serif text-stone-200 italic leading-relaxed">
                    "{currentCard.example_sentence}"
                  </p>
                </div>
              </div>

              {/* Bottom flip hint */}
              <div className="pt-3 border-t border-stone-800/80 flex items-center justify-center text-xs text-stone-500 space-x-1.5">
                <RotateCw size={14} className="text-amber-400/80" />
                <span>Clique para retornar à frente do cartão</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Navigation Controls */}
        <div className="w-full flex items-center justify-between mt-6 px-2">
          <button
            onClick={handlePrev}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl bg-stone-800 hover:bg-stone-700 text-stone-300 hover:text-white transition-all text-sm font-medium border border-stone-700/80"
          >
            <ChevronLeft size={18} />
            <span>Anterior</span>
          </button>

          <button
            onClick={handleFlip}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-stone-950 font-bold transition-all shadow-lg shadow-amber-500/20 hover:scale-105 active:scale-95 text-sm"
          >
            <RotateCw size={16} />
            <span>Virar Cartão</span>
          </button>

          <button
            onClick={handleNext}
            className="flex items-center space-x-1 px-4 py-2 rounded-xl bg-stone-800 hover:bg-stone-700 text-stone-300 hover:text-white transition-all text-sm font-medium border border-stone-700/80"
          >
            <span>Próximo</span>
            <ChevronRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
