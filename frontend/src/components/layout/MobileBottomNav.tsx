import React from 'react';
import { BookOpen, Map, Scroll, Bookmark, Swords, User as UserIcon } from 'lucide-react';

interface MobileBottomNavProps {
  currentTab: 'dashboard' | 'syllabus' | 'tabularium' | 'lexicon' | 'arena' | 'profile';
  onSelectTab: (tab: 'dashboard' | 'syllabus' | 'tabularium' | 'lexicon' | 'arena' | 'profile') => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  currentTab,
  onSelectTab,
}) => {
  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-30 border-t border-stone-200/90 bg-[#fdfbf7]/95 backdrop-blur-lg safe-bottom">
      <div className="grid grid-cols-6 h-14 items-center px-1">
        <button
          onClick={() => onSelectTab('dashboard')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'dashboard' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span className="text-[9px] uppercase tracking-wider">Aula</span>
        </button>

        <button
          onClick={() => onSelectTab('syllabus')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'syllabus' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <Map className="w-4 h-4" />
          <span className="text-[9px] uppercase tracking-wider">Trilha</span>
        </button>

        <button
          onClick={() => onSelectTab('tabularium')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'tabularium' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <Scroll className="w-4 h-4" />
          <span className="text-[9px] uppercase tracking-wider">Arquivo</span>
        </button>

        <button
          onClick={() => onSelectTab('lexicon')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'lexicon' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <Bookmark className="w-4 h-4" />
          <span className="text-[9px] uppercase tracking-wider">Lexicon</span>
        </button>

        <button
          onClick={() => onSelectTab('arena')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'arena' ? 'text-rose-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <Swords className="w-4 h-4 text-rose-600" />
          <span className="text-[9px] uppercase tracking-wider">Arena</span>
        </button>

        <button
          onClick={() => onSelectTab('profile')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'profile' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <UserIcon className="w-4 h-4" />
          <span className="text-[9px] uppercase tracking-wider">Perfil</span>
        </button>
      </div>
    </nav>
  );
};

