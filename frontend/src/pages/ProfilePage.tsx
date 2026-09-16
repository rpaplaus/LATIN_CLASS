import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useProgress } from '../context/ProgressContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Award, Flame, CheckCircle2, LogOut, ShieldCheck, Cpu } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user, logout } = useAuth();
  const { progress } = useProgress();

  return (
    <div className="space-y-6 max-w-2xl mx-auto animate-fadeIn">
      {/* Profile Header Card */}
      <Card className="p-6 border-stone-200 bg-white">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-900 font-serif font-bold text-2xl shadow-inner">
            {user?.full_name ? user.full_name[0].toUpperCase() : user?.email[0].toUpperCase() || 'D'}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-serif text-xl font-bold text-slate-900">
                {user?.full_name || 'Discipulus'}
              </h2>
              <Badge variant="warning" size="sm">
                Nível I (Tiro)
              </Badge>
            </div>
            <p className="text-sm text-stone-500 font-sans mt-0.5">{user?.email}</p>
          </div>
        </div>
      </Card>

      {/* Stats Summary */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="p-4 text-center border-stone-200">
          <Flame className="w-5 h-5 text-orange-500 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {progress?.current_streak_days || 1}d
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-400">Ofensiva</p>
        </Card>

        <Card className="p-4 text-center border-stone-200">
          <Award className="w-5 h-5 text-amber-600 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {progress?.total_points || 0}
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-400">Pontos</p>
        </Card>

        <Card className="p-4 text-center border-stone-200">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 mx-auto mb-1" />
          <p className="text-xl font-bold text-slate-900">
            {progress?.completed_lessons_count || 0}
          </p>
          <p className="text-[11px] uppercase tracking-wider text-stone-400">Lições</p>
        </Card>
      </div>

      {/* System Security & AI Engine info */}
      <Card className="p-5 border-stone-200 bg-stone-50 space-y-3">
        <h4 className="font-serif font-bold text-sm text-slate-800 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Segurança & Autenticação</span>
        </h4>
        <div className="text-xs text-stone-600 space-y-1.5">
          <p>
            • Sessão protegida com <strong>JWT curto + Refresh Token Rotation</strong> armazenado no Redis.
          </p>
          <p>
            • Arquitetura conteinerizada em Docker (PostgreSQL 16 + pgvector, Redis, FastAPI).
          </p>
          <p className="flex items-center gap-1.5 pt-1 text-amber-800 font-medium">
            <Cpu className="w-3.5 h-3.5 text-amber-600" />
            <span>Agente Magister Latium ativo e operando em LangGraph / LangChain</span>
          </p>
        </div>
      </Card>

      {/* Logout Action */}
      <div className="pt-4">
        <Button
          variant="outline"
          fullWidth
          size="lg"
          onClick={logout}
          className="text-red-700 border-red-200 hover:bg-red-50 hover:border-red-300"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Encerrar Sessão
        </Button>
      </div>
    </div>
  );
};
