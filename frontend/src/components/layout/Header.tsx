import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { useProgress } from '../../context/ProgressContext';
import { Flame, Award, LogOut, BookOpen, Map, Scroll, Bookmark, Swords, User as UserIcon } from 'lucide-react';

interface HeaderProps {
  currentTab?: 'dashboard' | 'syllabus' | 'tabularium' | 'lexicon' | 'arena' | 'profile';
  onSelectTab?: (tab: 'dashboard' | 'syllabus' | 'tabularium' | 'lexicon' | 'arena' | 'profile') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentTab, onSelectTab }) => {
  const { user, logout } = useAuth();
  const { progress } = useProgress();

  return (
    <header className="sticky top-0 z-30 w-full border-b border-stone-200/80 bg-[#fdfbf7]/90 backdrop-blur-md safe-top">
      <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => onSelectTab && onSelectTab('dashboard')}>
          <span className="text-2xl select-none" role="img" aria-label="Coliseu">
            🏛️
          </span>
          <div>
            <h1 className="font-serif font-bold text-lg tracking-wider text-slate-900 leading-none">
              LATIUM <span className="text-amber-600 font-sans text-xs uppercase tracking-widest ml-0.5">AI</span>
            </h1>
            <p className="text-[10px] uppercase tracking-widest text-stone-500 font-sans">
              Magister Latinae
            </p>
          </div>
        </div>

        {/* Desktop Navigation Links */}
        {user && onSelectTab && (
          <div className="hidden sm:flex items-center gap-1 bg-stone-100/90 p-1 rounded-xl border border-stone-200/80 text-xs font-semibold">
            <button
              onClick={() => onSelectTab('dashboard')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'dashboard'
                  ? 'bg-white text-stone-900 shadow-xs font-bold'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Aula</span>
            </button>

            <button
              onClick={() => onSelectTab('syllabus')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'syllabus'
                  ? 'bg-white text-stone-900 shadow-xs font-bold'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <Map className="w-3.5 h-3.5" />
              <span>Trilha</span>
            </button>

            <button
              onClick={() => onSelectTab('tabularium')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'tabularium'
                  ? 'bg-white text-amber-900 shadow-xs font-bold border border-amber-200/60'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <Scroll className="w-3.5 h-3.5 text-amber-700" />
              <span>Tabularium</span>
            </button>

            <button
              onClick={() => onSelectTab('lexicon')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'lexicon'
                  ? 'bg-white text-amber-900 shadow-xs font-bold border border-amber-200/60'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <Bookmark className="w-3.5 h-3.5 text-amber-700" />
              <span>Lexicon</span>
            </button>

            <button
              onClick={() => onSelectTab('arena')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'arena'
                  ? 'bg-white text-rose-900 shadow-xs font-bold border border-rose-200/80'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <Swords className="w-3.5 h-3.5 text-rose-700" />
              <span>Arena</span>
            </button>

            <button
              onClick={() => onSelectTab('profile')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center gap-1.5 ${
                currentTab === 'profile'
                  ? 'bg-white text-stone-900 shadow-xs font-bold'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <UserIcon className="w-3.5 h-3.5" />
              <span>Perfil</span>
            </button>
          </div>
        )}

        {/* User Stats & Logout */}
        {user && (
          <div className="flex items-center gap-2 sm:gap-4">
            {/* Streak */}
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-orange-50 border border-orange-200 text-orange-700 text-xs font-semibold">
              <Flame className="w-3.5 h-3.5 fill-orange-500 text-orange-600 animate-pulse" />
              <span>{progress?.current_streak_days || 1}d</span>
            </div>

            {/* Points */}
            <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold">
              <Award className="w-3.5 h-3.5 text-amber-600" />
              <span>{progress?.total_points || 0} pts</span>
            </div>

            {/* Logout button (desktop / header) */}
            <button
              onClick={logout}
              title="Encerrar Sessão"
              className="p-2 rounded-xl text-stone-500 hover:text-stone-800 hover:bg-stone-200/60 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
