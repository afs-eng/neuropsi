"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Brain, User, Mail, Lock, ArrowRight, Loader2, Phone, Briefcase, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    full_name: "",
    username: "",
    email: "",
    password: "",
    sex: "F",
    phone: "",
    crp: "",
    specialty: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (formData.password !== confirmPassword) {
      setError("As senhas digitadas nao coincidem.");
      setLoading(false);
      return;
    }

    try {
      const { api } = await import("@/lib/api");
      const response = await api.post<{ success: boolean; message: string }>("/api/accounts/register", formData);

      if (response.success) {
        setSuccess(true);
        setTimeout(() => {
          router.push("/login");
        }, 3000);
      }
    } catch (err: any) {
      console.error("Registration error:", err);
      setError(err?.message || "Erro ao criar conta. Verifique os dados.");
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-slate-200 p-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 mx-auto mb-6">
            <User className="h-8 w-8 text-emerald-600" />
          </div>
          <h2 className="text-2xl font-semibold text-slate-900 mb-2">Conta Criada!</h2>
          <p className="text-slate-500 mb-6">Sua conta foi criada com sucesso. Você será redirecionado para o login em instantes.</p>
          <Button onClick={() => router.push("/login")} className="w-full bg-indigo-600 hover:bg-indigo-700">
            Ir para Login agora
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <div className="flex w-full items-center justify-center p-8">
        <div className="w-full max-w-2xl bg-white rounded-2xl shadow-sm border border-slate-200 p-12">
          <div className="flex items-center gap-3 mb-10 justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-600">
              <Brain className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-semibold text-slate-900">NeuroAvalia</span>
          </div>

          <div className="mb-10 text-center">
            <h2 className="text-2xl font-semibold text-slate-900">Crie sua conta profissional</h2>
            <p className="mt-2 text-sm text-slate-500">Junte-se à plataforma de avaliações neuropsicológicas</p>
          </div>

          <form onSubmit={handleRegister} className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {error && (
              <div className="md:col-span-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Nome Completo</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  name="full_name"
                  placeholder="Seu nome completo"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="h-11 pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Nome de Usuário</label>
              <Input
                name="username"
                placeholder="Ex: joaosilva"
                value={formData.username}
                onChange={handleChange}
                className="h-11"
                required
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Email Profissional</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  name="email"
                  type="email"
                  placeholder="seu@email.com"
                  value={formData.email}
                  onChange={handleChange}
                  className="h-11 pl-10"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={handleChange}
                  className="h-11 pl-10 pr-11"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-600"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="text-xs text-slate-500">Use o icone ao lado para revisar e editar a senha antes de finalizar o cadastro.</p>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Confirmar Senha</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Repita sua senha"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="h-11 pl-10 pr-11"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-600"
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Telefone / WhatsApp</label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  name="phone"
                  placeholder="(00) 00000-0000"
                  value={formData.phone}
                  onChange={handleChange}
                  className="h-11 pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Sexo</label>
              <select
                name="sex"
                value={formData.sex}
                onChange={handleChange}
                className="h-11 w-full rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 shadow-sm outline-none transition-colors focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
                required
              >
                <option value="F">Feminino</option>
                <option value="M">Masculino</option>
                <option value="O">Outro</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Registro (CRP)</label>
              <div className="relative">
                <Briefcase className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  name="crp"
                  placeholder="CRP 00/0000"
                  value={formData.crp}
                  onChange={handleChange}
                  className="h-11 pl-10"
                />
              </div>
            </div>

            <div className="md:col-span-2 space-y-2">
                <label className="text-sm font-medium text-slate-700">Especialidade / Foco Clínico</label>
                <Input
                  name="specialty"
                  placeholder="Ex: Avaliação TEA, TDAH, Neuropsicologia do Envelhecimento"
                  value={formData.specialty}
                  onChange={handleChange}
                  className="h-11"
                />
            </div>

            <div className="md:col-span-2 pt-4">
              <Button type="submit" className="h-11 w-full gap-2 bg-indigo-600 hover:bg-indigo-700" disabled={loading}>
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    Finalizar Cadastro
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </Button>
            </div>
          </form>

          <p className="mt-8 text-center text-sm text-slate-500">
            Já possui uma conta?{" "}
            <Link href="/login" className="font-medium text-indigo-600 hover:text-indigo-700">
              Entrar agora
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
