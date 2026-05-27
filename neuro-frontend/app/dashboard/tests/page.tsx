"use client";

import { useRouter } from "next/navigation";
import { PageContainer, PageHeader, SectionCard, EmptyState } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FlaskConical, Play, Settings, Search, Filter, Info, BookOpen, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Instrument {
  code: string;
  name: string;
  category: string;
  description?: string;
  is_active: boolean;
}

export default function TestsPage() {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState("");
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchInstruments() {
      try {
        const data = await api.get<Instrument[]>("/api/tests/instruments");
        setInstruments(data);
      } catch (error) {
        console.error("Erro ao buscar instrumentos:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchInstruments();
  }, []);

  const filteredTests = instruments.filter((t) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleApplyTest = (testCode: string) => {
    router.push(`/dashboard/tests/quick?test=${testCode.replace(/_/g, "-")}`);
  };

  return (
    <PageContainer>
      <PageHeader
        title="Biblioteca de Instrumentos"
        subtitle="Catalogação técnica de testes psicométricos e escalas clínicas."
        actions={
          <div className="flex gap-2">
             <Button className="h-11 rounded-xl font-bold gap-2" onClick={() => router.push('/dashboard/tests/quick')}>
               <Play className="h-4 w-4" /> Teste rapido
             </Button>
             <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 group-focus-within:text-primary transition-colors" />
                <input 
                  type="text" 
                  placeholder="Buscar instrumento..." 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 h-11 w-64 rounded-xl border border-slate-200 bg-white text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                />
             </div>
             <Button variant="outline" className="h-11 rounded-xl border-slate-200 text-slate-500 font-bold gap-2">
               <Filter className="h-4 w-4" /> Filtros
             </Button>
          </div>
        }
      />

      {loading ? (
        <div className="flex items-center justify-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <span className="ml-3 text-sm font-medium text-slate-500">Carregando instrumentos...</span>
        </div>
      ) : filteredTests.length === 0 ? (
        <EmptyState 
          title="Nenhum teste encontrado" 
          description="Ajuste sua busca ou limpe os filtros para ver todos os instrumentos." 
          icon={<FlaskConical className="h-12 w-12 text-slate-200" />}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
          {filteredTests.map((test) => (
            <div key={test.code} className="group flex flex-col p-6 rounded-[32px] border border-slate-100 bg-white hover:border-primary/20 hover:shadow-spike transition-all relative overflow-hidden">
               {/* Background Pattern */}
              <div className="absolute top-0 right-0 p-8 opacity-[0.03] group-hover:opacity-[0.08] transition-opacity">
                <FlaskConical className="h-24 w-24 -mr-6 -mt-6" />
              </div>

              <div className="flex items-start justify-between mb-6">
                <div className="h-12 w-12 rounded-2xl bg-primary/5 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-all">
                  <BookOpen className="h-6 w-6" />
                </div>
                <Badge className="bg-primary/5 text-primary border-none rounded-full px-3 py-1 text-[9px] font-black uppercase tracking-widest">
                  {test.category}
                </Badge>
              </div>

              <div className="flex-1">
                <h3 className="text-xl font-black tracking-tight text-slate-900 mb-2">{test.name}</h3>
                <p className="text-sm font-medium text-slate-500 leading-relaxed mb-8">
                  {test.description}
                </p>
              </div>

              <div className="pt-6 border-t border-slate-50 flex gap-2">
                <Button 
                  className="flex-1 h-12 rounded-2xl font-black uppercase tracking-widest gap-2 shadow-sm border-none text-white"
                  onClick={() => handleApplyTest(test.code)}
                >
                  <Play className="h-4 w-4 fill-current" /> Aplicar
                </Button>
                <Button 
                  variant="ghost" 
                  size="icon"
                  className="h-12 w-12 rounded-2xl text-slate-300 hover:text-slate-600 hover:bg-slate-50 transition-all border border-slate-50 hover:border-slate-200"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-10 rounded-[32px] border border-indigo-200 bg-indigo-50 p-6 text-indigo-900">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h4 className="text-lg font-bold">Aplicacao sem montar avaliacao manualmente</h4>
            <p className="mt-1 text-sm text-indigo-800">
              Use o fluxo de <span className="font-semibold">Teste rapido</span> para escolher o instrumento, cadastrar os dados do paciente e abrir o formulario ja pronto para gerar a analise e exportar em PDF na tela de resultado.
            </p>
          </div>
          <Button className="rounded-2xl" onClick={() => router.push('/dashboard/tests/quick')}>
            Iniciar teste rapido
          </Button>
        </div>
      </div>

      {/* Info Card Sidebar Style */}
      <div className="mt-12 p-8 rounded-[40px] bg-slate-900 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-8 animate-in zoom-in-95 duration-1000">
         <div className="flex items-center gap-6">
            <div className="h-14 w-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
               <Info className="h-7 w-7" />
            </div>
            <div className="space-y-1">
               <h4 className="text-lg font-bold text-white">Base Normativa 2025</h4>
               <p className="text-sm text-slate-400 max-w-md">Todos os instrumentos são atualizados mensalmente com as normas populacionais mais recentes do SATEPSI.</p>
            </div>
         </div>
         <Button variant="outline" className="h-14 px-8 rounded-2xl border-slate-700 text-white font-black uppercase tracking-widest hover:bg-slate-800 transition-colors">
            Solicitar Novo Teste
         </Button>
      </div>
    </PageContainer>
  );
}
