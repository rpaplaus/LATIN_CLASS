import React from 'react';
import { BookOpen, Map, User as UserIcon } from 'lucide-react';

interface MobileBottomNavProps {
  currentTab: 'dashboard' | 'syllabus' | 'profile';
  onSelectTab: (tab: 'dashboard' | 'syllabus' | 'profile') => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  currentTab,
  onSelectTab,
}) => {
  return (
    <nav className="sm:hidden fixed bottom-0 left-0 right-0 z-30 border-t border-stone-200/90 bg-[#fdfbf7]/95 backdrop-blur-lg safe-bottom">
      <div className="grid grid-cols-3 h-14 items-center px-4">
        <button
          onClick={() => onSelectTab('dashboard')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'dashboard' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <BookOpen className="w-5 h-5" />
          <span className="text-[10px] uppercase tracking-wider">Aula</span>
        </button>

        <button
          onClick={() => onSelectTab('syllabus')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'syllabus' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <Map className="w-5 h-5" />
          <span className="text-[10px] uppercase tracking-wider">Trilha</span>
        </button>

        <button
          onClick={() => onSelectTab('profile')}
          className={`flex flex-col items-center justify-center gap-1 transition-colors ${
            currentTab === 'profile' ? 'text-amber-700 font-semibold' : 'text-stone-400 hover:text-stone-600'
          }`}
        >
          <UserIcon className="w-5 h-5" />
          <span className="text-[10px] uppercase tracking-wider">Perfil</span>
        </button>
      </div>
    </nav>
  );
};
