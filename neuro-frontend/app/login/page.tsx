"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Brain, Mail, Lock, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { QRCodeSVG } from "qrcode.react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [twoFactorCode, setTwoFactorCode] = useState("");
  const [challengeToken, setChallengeToken] = useState("");
  const [challengeOtpauthUrl, setChallengeOtpauthUrl] = useState("");
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [challengeSetupRequired, setChallengeSetupRequired] = useState(false);
  const [awaitingTwoFactor, setAwaitingTwoFactor] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [twoFactorAttempts, setTwoFactorAttempts] = useState(0);
  const [showBackupInput, setShowBackupInput] = useState(false);
  const MAX_2FA_ATTEMPTS = 3;

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const identifier = email.trim();

    try {
      const { api } = await import("@/lib/api");
      const response = await api.post<{
        access?: string;
        user?: any;
        two_factor_required?: boolean;
        two_factor_setup_required?: boolean;
        challenge_token?: string;
        otpauth_url?: string;
        secret?: string;
        backup_codes?: string[];
      }>("/api/accounts/login", {
        email: identifier,
        password: password,
      });

      if (response.access) {
        localStorage.setItem("token", response.access);
        localStorage.setItem("user", JSON.stringify(response.user));
        router.push("/dashboard");
        return;
      }

      if (response.two_factor_required && response.challenge_token) {
        setChallengeToken(response.challenge_token);
        setChallengeSetupRequired(Boolean(response.two_factor_setup_required));
        setChallengeOtpauthUrl(response.otpauth_url || "");
        setBackupCodes(response.backup_codes || []);
        setAwaitingTwoFactor(true);
        setTwoFactorAttempts(0);
        setShowBackupInput(false);
        setError("");
        return;
      }
    } catch (err: any) {
      console.error("Login error:", err);
      setError(err?.message || "Credenciais inválidas. Tente novamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleTwoFactorSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const { api } = await import("@/lib/api");
      const response = await api.post<{
        access?: string;
        user?: any;
        backup_codes?: string[];
      }>("/api/accounts/login/2fa", {
        challenge_token: challengeToken,
        code: twoFactorCode,
      });

      if (response.access) {
        localStorage.setItem("token", response.access);
        localStorage.setItem("user", JSON.stringify(response.user));

        if (response.backup_codes?.length) {
          setBackupCodes(response.backup_codes);
          setSetupComplete(true);
          setAwaitingTwoFactor(false);
          return;
        }

        router.push("/dashboard");
      }
    } catch (err: any) {
      console.error("2FA error:", err);
      const newAttempts = twoFactorAttempts + 1;
      setTwoFactorAttempts(newAttempts);
      if (newAttempts >= MAX_2FA_ATTEMPTS) {
        setShowBackupInput(true);
        setError("Código inválido. Use um código de backup abaixo.");
      } else {
        setError(`Código 2FA inválido. Tentativa ${newAttempts} de ${MAX_2FA_ATTEMPTS}.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-indigo-600 via-indigo-700 to-indigo-800 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
              <Brain className="h-7 w-7 text-white" />
            </div>
            <span className="text-2xl font-semibold text-white">NeuroAvalia</span>
          </div>
        </div>

        <div className="max-w-lg">
          <h1 className="text-4xl font-semibold leading-tight text-white">
            Sistema clínico para avaliações neuropsicológicas
          </h1>
          <p className="mt-4 text-lg text-indigo-100">
            Organize suas avaliações, aplique testes padronizados e gere laudos profissionais com o apoio de IA assistiva.
          </p>
        </div>

        <div className="flex items-center gap-6 text-sm text-indigo-200">
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
            <span>Segurança de dados clínicos</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-emerald-400"></div>
            <span>Interface profesional</span>
          </div>
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex w-full items-center justify-center lg:w-1/2 bg-white p-8">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-semibold text-slate-900">NeuroAvalia</span>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-slate-900">Bem-vindo de volta</h2>
            <p className="mt-2 text-sm text-slate-500">
              {awaitingTwoFactor
                ? "Digite o código do seu autenticador para concluir o acesso."
                : "Entre com suas credenciais para acessar o sistema"}
            </p>
          </div>

          {setupComplete ? (
            <div className="space-y-5">
              <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                <p className="font-medium">2FA ativado com sucesso.</p>
                <p className="mt-1">Guarde seus códigos de backup abaixo.</p>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="font-medium text-slate-900">Códigos de backup</p>
                <ul className="mt-2 space-y-1 font-mono text-xs">
                  {backupCodes.map((code) => (
                    <li key={code}>{code}</li>
                  ))}
                </ul>
              </div>
              <Button type="button" className="h-11 w-full gap-2" onClick={() => router.push("/dashboard")}>
                Ir para o painel
                <ArrowRight className="h-4 w-4" />
              </Button>
            </div>
          ) : awaitingTwoFactor ? (
            <form onSubmit={handleTwoFactorSubmit} className="space-y-5">
              {error && (
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {challengeSetupRequired && (
                <div className="rounded-lg border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm text-indigo-900 space-y-2">
                  <p className="font-medium">Configuração inicial de 2FA</p>
                  <p>Escaneie o QR code abaixo com seu autenticador.</p>
                  {challengeOtpauthUrl && (
                    <div className="flex justify-center rounded-md bg-white p-3 border border-indigo-100">
                      <QRCodeSVG value={challengeOtpauthUrl} size={160} />
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  {showBackupInput ? "Código de backup" : "Código 2FA"}
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    type="text"
                    inputMode={showBackupInput ? "text" : "numeric"}
                    autoComplete="one-time-code"
                    placeholder={showBackupInput ? "0000-0000-0000-0000" : "000000"}
                    value={twoFactorCode}
                    onChange={(e) => setTwoFactorCode(e.target.value)}
                    className="h-11 pl-10"
                    required
                  />
                </div>
              </div>

              {showBackupInput && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900 space-y-2">
                  <p className="font-medium">Perdeu o acesso ao autenticador?</p>
                  <p>Digite um dos códigos de backup gerados na ativação do 2FA. Cada código só pode ser usado uma vez.</p>
                </div>
              )}

              <Button type="submit" className="h-11 w-full gap-2" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Verificar código
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </form>
          ) : (
          <form onSubmit={handleLogin} className="space-y-5">
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  type="email"
                  placeholder="seu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-11 pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-slate-700">Senha</label>
                <Link href="/forgot-password" className="text-sm text-indigo-600 hover:text-indigo-700">
                  Esqueceu a senha?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 pl-10"
                  required
                />
              </div>
            </div>

            <Button type="submit" className="h-11 w-full gap-2" disabled={loading}>
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Entrar
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </form>
          )}

          <p className="mt-8 text-center text-sm text-slate-500">
            Não tem uma conta?{" "}
            <Link href="/register" className="font-medium text-indigo-600 hover:text-indigo-700">
              Criar conta agora
            </Link>
          </p>

          <p className="mt-4 text-center text-xs text-slate-400">
            Sistema para uso exclusivo de profissionais autorizados
          </p>

        </div>
      </div>
    </div>
  );
}
