import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { LogIn, UserPlus, AlertCircle, Sparkles, BookOpen } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const { login, register, error, clearError } = useAuth();
  const [isRegisterMode, setIsRegisterMode] = useState<boolean>(false);

  // Form states
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [fullName, setFullName] = useState<string>('');
  const [confirmPassword, setConfirmPassword] = useState<string>('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const switchMode = (regMode: boolean) => {
    setIsRegisterMode(regMode);
    clearError();
    setLocalError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email.trim() || !password) {
      setLocalError('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    if (isRegisterMode) {
      if (password.length < 8) {
        setLocalError('A senha deve conter no mínimo 8 caracteres.');
        return;
      }
      if (password !== confirmPassword) {
        setLocalError('As senhas digitadas não coincidem.');
        return;
      }
    }

    setIsSubmitting(true);
    try {
      if (isRegisterMode) {
        await register(email.trim(), password, fullName.trim() || undefined);
      } else {
        await login(email.trim(), password);
      }
    } catch {
      // Error handled by AuthContext or local catch
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <div className="min-h-screen bg-[#fbf9f4] flex flex-col justify-center items-center px-4 py-8 selection:bg-amber-200">
      {/* Background Decorative Roman Motif */}
      <div className="w-full max-w-md">
        {/* Header Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-100/80 border border-amber-300/60 shadow-sm mb-4">
            <span className="text-3xl select-none" role="img" aria-label="Coliseu">
              🏛️
            </span>
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl font-bold tracking-wider text-slate-900">
            LATIUM <span className="text-amber-600 font-sans text-xl tracking-normal">AI</span>
          </h1>
          <p className="text-stone-500 text-sm mt-1 font-serif italic">
            "Ars longa, vita brevis" — Tutor de Latim com Inteligência Artificial
          </p>
        </div>

        {/* Auth Card */}
        <Card className="p-6 sm:p-8 bg-white/95 shadow-xl border-stone-200/90 backdrop-blur-sm">
          {/* Mode Switch Tabs */}
          <div className="flex rounded-xl bg-stone-100 p-1 mb-6 border border-stone-200">
            <button
              type="button"
              onClick={() => switchMode(false)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                !isRegisterMode
                  ? 'bg-white text-stone-900 shadow-sm'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <LogIn className="w-4 h-4" />
              Entrar
            </button>
            <button
              type="button"
              onClick={() => switchMode(true)}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 text-xs font-semibold rounded-lg transition-all ${
                isRegisterMode
                  ? 'bg-white text-stone-900 shadow-sm'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <UserPlus className="w-4 h-4" />
              Criar Conta
            </button>
          </div>

          {/* Error Alert */}
          {activeError && (
            <div className="mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2.5 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
              <span>{activeError}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegisterMode && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                  Nome Completo (Opcional)
                </label>
                <Input
                  type="text"
                  placeholder="Marcus Aurelius"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  disabled={isSubmitting}
                  autoComplete="name"
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                E-mail ou Usuário
              </label>
              <Input
                type="email"
                placeholder="discipulus@roma.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isSubmitting}
                autoComplete="email"
                autoCapitalize="none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                Senha
              </label>
              <Input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isSubmitting}
                autoComplete={isRegisterMode ? 'new-password' : 'current-password'}
              />
              {isRegisterMode && (
                <p className="text-[11px] text-stone-400 mt-1">
                  Mínimo de 8 caracteres.
                </p>
              )}
            </div>

            {isRegisterMode && (
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-stone-600 mb-1.5">
                  Confirmar Senha
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={isSubmitting}
                  autoComplete="new-password"
                />
              </div>
            )}

            <div className="pt-2">
              <Button
                type="submit"
                variant="primary"
                fullWidth
                size="lg"
                isLoading={isSubmitting}
                className="shadow-md hover:shadow-lg"
              >
                {isRegisterMode ? 'Cadastrar e Iniciar Estudos' : 'Entrar na Sala de Aula'}
              </Button>
            </div>
          </form>

          {/* Quick Demo Helper */}
          <div className="mt-6 pt-5 border-t border-stone-100 text-center">
            <div className="inline-flex items-center gap-1.5 text-xs text-stone-500">
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
              <span>Sessão protegida por Refresh Token Rotation</span>
            </div>
          </div>
        </Card>

        {/* Footer info */}
        <p className="text-center text-xs text-stone-400 mt-6 flex items-center justify-center gap-1">
          <BookOpen className="w-3.5 h-3.5" /> Latium AI &copy; {new Date().getFullYear()} — Omnia vincit amor
        </p>
      </div>
    </div>
  );
};
