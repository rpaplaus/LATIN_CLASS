import React, { useState, useEffect } from 'react';
import {
  X,
  Shield,
  Flame,
  Award,
  Scroll,
  Crown,
  BookOpen,
  Sparkles,
  Lock,
  CheckCircle2,
  Trophy,
} from 'lucide-react';
import { badgeApi } from '../../api/badgeApi';
import { SenateBadgeItem, SenateOverview } from '../../types/gamification';

interface SenateBadgesModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SenateBadgesModal: React.FC<SenateBadgesModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [overview, setOverview] = useState<SenateOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    if (!isOpen) return;

    const fetchBadges = async () => {
      setLoading(true);
      try {
        const data = await badgeApi.getSenateOverview();
        setOverview(data);
      } catch (err) {
        console.error('Erro ao carregar comendas do Senado:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchBadges();
  }, [isOpen]);

  if (!isOpen) return null;

  const renderBadgeIcon = (iconName: string, isUnlocked: boolean, size = 28) => {
    const colorClass = isUnlocked ? 'text-amber-400' : 'text-stone-500';
    switch (iconName) {
      case 'Flame':
        return <Flame size={size} className={colorClass} />;
      case 'Award':
        return <Award size={size} className={colorClass} />;
      case 'Scroll':
        return <Scroll size={size} className={colorClass} />;
      case 'Crown':
        return <Crown size={size} className={colorClass} />;
      case 'BookOpen':
        return <BookOpen size={size} className={colorClass} />;
      case 'Sparkles':
        return <Sparkles size={size} className={colorClass} />;
      case 'Shield':
      default:
        return <Shield size={size} className={colorClass} />;
    }
  };

  const filteredBadges = overview?.badges.filter((item) => {
    if (selectedCategory === 'all') return true;
    return item.badge.category === selectedCategory;
  }) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-stone-900 border-2 border-amber-500/40 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Imperial Header */}
        <div className="relative bg-gradient-to-r from-red-950 via-stone-900 to-amber-950 p-6 border-b border-amber-500/30">
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-full bg-black/40 hover:bg-black/60 text-stone-300 hover:text-white transition-colors"
            aria-label="Fechar Galeria"
          >
            <X size={20} />
          </button>

          <div className="flex items-center space-x-3 mb-2">
            <div className="p-2.5 rounded-2xl bg-amber-500/20 border border-amber-500/40 text-amber-300">
              <Trophy size={24} />
            </div>
            <div>
              <span className="text-xs uppercase tracking-widest text-amber-400 font-serif font-bold">
                • SENATUS LATIUM •
              </span>
              <h2 className="text-2xl font-serif font-bold text-stone-100 tracking-wide">
                Galeria de Comendas & Honrarias
              </h2>
            </div>
          </div>

          {/* Progress Bar */}
          {overview && (
            <div className="mt-4 p-3 rounded-xl bg-black/30 border border-stone-800">
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-stone-300 font-medium">
                  Comendas Conquistadas:{' '}
                  <span className="text-amber-400 font-bold">
                    {overview.total_unlocked}
                  </span>{' '}
                  de {overview.total_available}
                </span>
                <span className="text-amber-400 font-bold">
                  {overview.completion_percentage}%
                </span>
              </div>
              <div className="w-full h-2.5 rounded-full bg-stone-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-amber-600 via-amber-500 to-yellow-300 rounded-full transition-all duration-500"
                  style={{ width: `${overview.completion_percentage}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Category Filters */}
        <div className="flex items-center space-x-2 px-6 py-3 bg-stone-950/60 border-b border-stone-800/80 overflow-x-auto text-xs font-medium">
          {[
            { id: 'all', label: 'Todas' },
            { id: 'completion', label: 'Conclusão' },
            { id: 'streak', label: 'Ofensiva (Streak)' },
            { id: 'score', label: 'Maestria & Pontos' },
            { id: 'special', label: 'Especiais' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-all ${
                selectedCategory === cat.id
                  ? 'bg-amber-500 text-stone-950 font-bold shadow-md shadow-amber-500/20'
                  : 'text-stone-400 hover:text-stone-200 hover:bg-stone-800'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Badges Grid */}
        <div className="p-6 overflow-y-auto space-y-4">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-12 text-stone-400">
              <Sparkles className="animate-spin text-amber-400 mb-2" size={28} />
              <p className="text-sm font-serif">Consultando registros do Senado...</p>
            </div>
          ) : filteredBadges.length === 0 ? (
            <p className="text-center py-8 text-stone-500 text-sm">
              Nenhuma honraria nesta categoria.
            </p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredBadges.map((item: SenateBadgeItem) => {
                const { badge, is_unlocked, progress } = item;
                return (
                  <div
                    key={badge.id}
                    className={`relative p-4 rounded-2xl border transition-all duration-300 flex items-start space-x-4 ${
                      is_unlocked
                        ? 'bg-gradient-to-b from-stone-800/90 to-amber-950/20 border-amber-500/40 shadow-lg shadow-amber-950/20'
                        : 'bg-stone-950/40 border-stone-800/80 opacity-70'
                    }`}
                  >
                    {/* Badge Medallion Icon */}
                    <div
                      className={`relative flex-shrink-0 w-14 h-14 rounded-2xl flex items-center justify-center border shadow-inner ${
                        is_unlocked
                          ? 'bg-gradient-to-br from-amber-500/20 via-stone-800 to-amber-950/40 border-amber-400/60 shadow-amber-500/20'
                          : 'bg-stone-900 border-stone-800'
                      }`}
                    >
                      {renderBadgeIcon(badge.icon_name, is_unlocked)}

                      {/* Corner checkmark or lock indicator */}
                      <div className="absolute -top-1.5 -right-1.5">
                        {is_unlocked ? (
                          <CheckCircle2
                            size={18}
                            className="text-amber-400 bg-stone-900 rounded-full fill-amber-900"
                          />
                        ) : (
                          <div className="p-0.5 bg-stone-900 rounded-full border border-stone-700">
                            <Lock size={12} className="text-stone-400" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Badge Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h4
                          className={`font-serif font-bold text-base truncate ${
                            is_unlocked ? 'text-amber-300' : 'text-stone-300'
                          }`}
                        >
                          {badge.title}
                        </h4>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 font-mono font-bold">
                          +{badge.xp_reward} XP
                        </span>
                      </div>

                      {/* Latin Motto */}
                      <p className="text-xs font-serif italic text-amber-200/70 mb-1">
                        "{badge.latin_motto}"
                      </p>

                      <p className="text-xs text-stone-400 leading-relaxed mb-2">
                        {badge.description}
                      </p>

                      {/* Progress / Status */}
                      {!is_unlocked && badge.requirement_value > 1 && (
                        <div className="text-xs text-stone-500">
                          Progresso:{' '}
                          <span className="text-stone-300 font-semibold">
                            {progress} / {badge.requirement_value}
                          </span>
                        </div>
                      )}

                      {is_unlocked && item.unlocked_at && (
                        <div className="text-[11px] text-amber-400/80 font-mono">
                          Conquistado em{' '}
                          {new Date(item.unlocked_at).toLocaleDateString('pt-BR')}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
