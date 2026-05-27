"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { PageContainer, PageHeader, SectionCard, InfoCard, StatCard, EmptyState } from "@/components/ui/page";
import { Button } from "@/components/ui/button";
import {
  ArrowLeft,
  User,
  Calendar,
  FileText,
  ClipboardList,
  FolderOpen,
  StickyNote,
  Plus,
  X,
  Send,
  Mail,
  MessageCircle,
  Copy,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  AlertCircle,
  Clock,
  ShieldCheck,
  LayoutDashboard,
  Edit,
  Printer
  ,Trash2
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { api, resolveApiUrl } from "@/lib/api";
import { getEvaluationDeadlineMeta } from "@/lib/evaluation-deadline";
import { AnamnesisResponseViewer } from "@/components/anamnesis/AnamnesisResponseViewer";
import { TestWorkflowBadge } from "@/components/tests/TestWorkflowBadge";

interface Instrument {
  id: number;
  code: string;
  name: string;
  category: string;
  version: string;
  is_active: boolean;
  min_age?: number | null;
  max_age?: number | null;
  age_message?: string;
}

interface Evaluation {
  id: number;
  code: string;
  title: string;
  patient_id: number;
  patient_name: string;
  patient_birth_date: string | null;
  patient_sex: string | null;
  patient_responsible_name: string | null;
  examiner_name: string | null;
  referral_reason: string;
  evaluation_purpose: string;
  clinical_hypothesis: string;
  start_date: string | null;
  end_date: string | null;
  status: string;
  status_display: string;
  priority: string;
  priority_display: string;
  is_archived: boolean;
  general_notes: string;
  tests: TestApp[];
  documents: any[];
  progress_entries: ProgressEntry[];
  current_anamnesis?: CurrentAnamnesisSummary | null;
  clinical_checklist: ClinicalChecklist;
  created_at: string;
}

interface TestApp {
  id: number;
  instrument_name: string;
  instrument_code: string;
  applied_on: string | null;
  is_validated: boolean;
  status: string;
  status_display?: string | null;
  raw_payload?: Record<string, unknown>;
  classified_payload?: Record<string, unknown>;
}

interface EvaluationDocument {
  id: number;
  evaluation_id: number;
  patient_id: number;
  title: string;
  file_name: string;
  file_url: string;
  document_type: string;
  document_type_display: string;
  source: string;
  document_date: string | null;
  notes: string;
  is_relevant_for_report: boolean;
  created_at: string;
}

interface ProgressEntry {
  id: number;
  evaluation_id: number;
  patient_id: number;
  professional_id: number;
  professional_name: string;
  entry_type: string;
  entry_type_display: string;
  entry_date: string;
  start_time: string | null;
  end_time: string | null;
  objective: string;
  tests_applied: string;
  observed_behavior: string;
  clinical_notes: string;
  next_steps: string;
  include_in_report: boolean;
  created_at: string;
}

interface CurrentAnamnesisSummary {
  response_id: number;
  status: string;
  source: string;
  response_type: string;
  template_name: string;
  submitted_by_name: string;
  submitted_by_relation: string;
  submitted_at: string | null;
  reviewed_at: string | null;
  summary_payload: Record<string, any>;
}

interface ClinicalChecklist {
  anamnesis_completed: boolean;
  anamnesis_reviewed: boolean;
  has_relevant_documents: boolean;
  has_progress_entries_for_report: boolean;
  has_validated_tests: boolean;
  ready_for_report: boolean;
}

interface ReportSection {
  id: number;
  key: string;
  title: string;
  order: number;
  source_payload: Record<string, unknown>;
  generated_text: string;
  edited_text: string;
  is_locked: boolean;
}

interface ReportItem {
  id: number;
  evaluation_id: number;
  evaluation_code: string;
  evaluation_title: string;
  patient_id: number;
  author_id: number;
  author_name: string;
  title: string;
  interested_party: string;
  purpose: string;
  status: string;
  snapshot_payload: Record<string, unknown>;
  final_text: string;
  created_at: string;
  updated_at: string;
  sections?: ReportSection[];
}

interface AnamnesisTemplate {
  id: number;
  code: string;
  name: string;
  target_type: string;
  version: string;
  schema_payload: Record<string, any>;
  is_active: boolean;
}

interface AnamnesisInvite {
  id: number;
  evaluation_id: number;
  patient_id: number;
  template_id: number;
  template_name: string;
  template_target_type: string;
  recipient_name: string;
  recipient_email: string;
  recipient_phone: string;
  channel: string;
  token: string;
  public_url: string;
  status: string;
  sent_at: string | null;
  opened_at: string | null;
  last_activity_at: string | null;
  completed_at: string | null;
  expires_at: string | null;
  created_by_name: string;
  created_at: string;
  message: string;
  delivery_payload: Record<string, any>;
}

interface AnamnesisResponse {
  id: number;
  invite_id: number;
  evaluation_id: number;
  patient_id: number;
  template_id: number;
  template_name: string;
  answers_payload: Record<string, any>;
  status: string;
  submitted_by_name: string;
  submitted_by_relation: string;
  submitted_at: string | null;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-600 border-slate-200",
  collecting_data: "bg-amber-50 text-amber-600 border-amber-100",
  tests_in_progress: "bg-blue-50 text-blue-600 border-blue-100",
  scoring: "bg-purple-50 text-purple-600 border-purple-100",
  writing_report: "bg-orange-50 text-orange-600 border-orange-100",
  in_review: "bg-indigo-50 text-indigo-600 border-indigo-100",
  approved: "bg-emerald-50 text-emerald-600 border-emerald-100",
  archived: "bg-slate-100 text-slate-400 border-slate-200",
};

type TabType = "overview" | "tests" | "anamnesis" | "documents" | "evolution" | "report";

export default function EvaluationDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>("overview");
  const [showAddTestModal, setShowAddTestModal] = useState(false);
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loadingInstruments, setLoadingInstruments] = useState(false);
  const [addingTest, setAddingTest] = useState(false);
  const [instrumentFilterError, setInstrumentFilterError] = useState<string | null>(null);
  const [selectedInstrumentIds, setSelectedInstrumentIds] = useState<number[]>([]);
  const [documents, setDocuments] = useState<EvaluationDocument[]>([]);
  const [anamnesisTemplates, setAnamnesisTemplates] = useState<AnamnesisTemplate[]>([]);
  const [anamnesisInvites, setAnamnesisInvites] = useState<AnamnesisInvite[]>([]);
  const [anamnesisResponses, setAnamnesisResponses] = useState<AnamnesisResponse[]>([]);
  const [selectedAnamnesisResponse, setSelectedAnamnesisResponse] = useState<AnamnesisResponse | null>(null);
  const [progressEntries, setProgressEntries] = useState<ProgressEntry[]>([]);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [selectedReport, setSelectedReport] = useState<ReportItem | null>(null);
  const [tabLoading, setTabLoading] = useState(false);
  const [pageNotice, setPageNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [showDocumentForm, setShowDocumentForm] = useState(false);
  const [showAnamnesisInviteForm, setShowAnamnesisInviteForm] = useState(false);
  const [showProgressForm, setShowProgressForm] = useState(false);
  const [showReportForm, setShowReportForm] = useState(false);
  const [deleteReportId, setDeleteReportId] = useState<number | null>(null);
  const [deleteReportConfirmationOpen, setDeleteReportConfirmationOpen] = useState(false);
  const [savingDocument, setSavingDocument] = useState(false);
  const [savingAnamnesisInvite, setSavingAnamnesisInvite] = useState(false);
  const [savingProgress, setSavingProgress] = useState(false);
  const [savingReport, setSavingReport] = useState(false);
  const [deletingReport, setDeletingReport] = useState(false);
  const [documentForm, setDocumentForm] = useState({
    title: "",
    document_type: "other",
    source: "",
    document_date: "",
    notes: "",
    is_relevant_for_report: true,
    file: null as File | null,
  });
  const [anamnesisForm, setAnamnesisForm] = useState({
    template_id: "",
    recipient_name: "",
    recipient_email: "",
    recipient_phone: "",
    channel: "email",
    expires_at: "",
    message: "",
  });
  const [progressForm, setProgressForm] = useState({
    entry_type: "anamnesis",
    entry_date: new Date().toISOString().slice(0, 10),
    start_time: "",
    end_time: "",
    objective: "",
    tests_applied: "",
    observed_behavior: "",
    clinical_notes: "",
    next_steps: "",
    include_in_report: true,
  });
  const [reportForm, setReportForm] = useState({
    title: "",
    interested_party: "",
    purpose: "",
  });

  const documentRequiredMissing = !documentForm.title || !documentForm.file;
  const anamnesisRequiredMissing = !anamnesisForm.template_id || !anamnesisForm.recipient_name || (!anamnesisForm.recipient_email && !anamnesisForm.recipient_phone);
  const progressRequiredMissing = !progressForm.entry_type || !progressForm.entry_date;
  const reportRequiredMissing = !reportForm.title;

  function isValidTab(value: string | null): value is TabType {
    return value === "overview" || value === "tests" || value === "anamnesis" || value === "documents" || value === "evolution" || value === "report";
  }

  function navigateToTab(tab: TabType) {
    setActiveTab(tab);
    window.history.pushState(null, '', `/dashboard/evaluations/${params.id}/overview?tab=${tab}`);
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    const search = new URLSearchParams(window.location.search);
    const tab = search.get("tab");
    if (isValidTab(tab)) {
      setActiveTab(tab);
    }
  }, []);

  useEffect(() => {
    async function fetchEvaluation() {
      try {
        setErrorMessage(null);
        const data = await api.get<Evaluation>(`/api/evaluations/${params.id}`);
        setEvaluation(data);
      } catch (err: any) {
        console.error("Erro ao buscar avaliação:", err);
        if (err?.status === 401 || err?.status === 403) {
          setErrorMessage("Sua sessão não tem permissão para acessar esta avaliação. Faça login novamente.");
        } else {
          setErrorMessage(err?.message || "Não foi possível carregar a avaliação.");
        }
      } finally {
        setLoading(false);
      }
    }
    if (params.id) {
      fetchEvaluation();
    }
  }, [params.id]);

  useEffect(() => {
    if (!evaluation) return;
    if (activeTab === "anamnesis") loadAnamnesisData();
    if (activeTab === "documents") loadDocuments();
    if (activeTab === "evolution") loadProgressEntries();
    if (activeTab === "report") loadReports();
    if (activeTab === "tests") loadInstruments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, evaluation]);

  async function loadInstruments() {
    setLoadingInstruments(true);
    try {
      const data = await api.get<Instrument[]>("/api/tests/instruments");
      setInstruments(data);
    } catch (err: any) {
      console.error("Erro ao carregar instrumentos:", err);
      alert("Erro ao carregar instrumentos: " + (err?.message || "Ver console"));
    } finally {
      setLoadingInstruments(false);
    }
  }

  async function addTest(instrumentId: number) {
    if (!evaluation) return;
    setAddingTest(true);
    try {
      setInstrumentFilterError(null);
      const newTest = await api.post<any>("/api/tests/applications", {
        evaluation_id: evaluation.id,
        instrument_id: instrumentId,
      });
      setEvaluation({
        ...evaluation,
        tests: [...evaluation.tests, {
          id: newTest.id,
          instrument_name: newTest.instrument_name,
          instrument_code: newTest.instrument_code,
          applied_on: newTest.applied_on,
          is_validated: newTest.is_validated,
          status: newTest.is_validated ? "Concluído" : "Pendente"
        }]
      });
      setShowAddTestModal(false);
    } catch (err: any) {
      console.error("Erro ao adicionar teste:", err);
      setInstrumentFilterError(err?.message || "Erro ao adicionar teste.");
    } finally {
      setAddingTest(false);
    }
  }

  async function loadDocuments() {
    if (!evaluation) return;
    setTabLoading(true);
    try {
      const data = await api.get<EvaluationDocument[]>(`/api/documents/list?evaluation_id=${evaluation.id}`);
      setDocuments(data);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao carregar documentos." });
    } finally {
      setTabLoading(false);
    }
  }

  async function loadAnamnesisData() {
    if (!evaluation) return;
    setTabLoading(true);
    try {
      const [templates, invites, responses] = await Promise.all([
        api.get<AnamnesisTemplate[]>("/api/anamnesis/templates"),
        api.get<AnamnesisInvite[]>(`/api/anamnesis/invites?evaluation_id=${evaluation.id}`),
        api.get<AnamnesisResponse[]>(`/api/anamnesis/responses?evaluation_id=${evaluation.id}`),
      ]);
      setAnamnesisTemplates(templates);
      setAnamnesisInvites(invites);
      setAnamnesisResponses(responses);
      setSelectedAnamnesisResponse((current) => current ? responses.find((item) => item.id === current.id) || null : responses[0] || null);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao carregar anamneses." });
    } finally {
      setTabLoading(false);
    }
  }

  async function handleCreateAnamnesisInvite() {
    if (!evaluation || anamnesisRequiredMissing) return;
    setSavingAnamnesisInvite(true);
    try {
      const invite = await api.post<AnamnesisInvite>("/api/anamnesis/invites", {
        evaluation_id: evaluation.id,
        patient_id: evaluation.patient_id,
        template_id: Number(anamnesisForm.template_id),
        recipient_name: anamnesisForm.recipient_name,
        recipient_email: anamnesisForm.recipient_email,
        recipient_phone: anamnesisForm.recipient_phone,
        channel: anamnesisForm.channel,
        message: anamnesisForm.message,
        expires_at: anamnesisForm.expires_at ? new Date(anamnesisForm.expires_at).toISOString() : null,
      });
      setShowAnamnesisInviteForm(false);
      setAnamnesisForm({ template_id: "", recipient_name: "", recipient_email: "", recipient_phone: "", channel: "email", expires_at: "", message: "" });
      await handleSendAnamnesis(invite.id, invite.channel as "email" | "whatsapp");
      await loadAnamnesisData();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao criar convite de anamnese." });
    } finally {
      setSavingAnamnesisInvite(false);
    }
  }

  async function handleSendAnamnesis(inviteId: number, channel: "email" | "whatsapp") {
    try {
      const endpoint = channel === "email" ? `/api/anamnesis/invites/${inviteId}/send-email` : `/api/anamnesis/invites/${inviteId}/send-whatsapp`;
      const invite = await api.post<AnamnesisInvite>(endpoint, {});
      const payload = invite.delivery_payload || {};

      if (channel === "email") {
        const provider = payload.provider === "resend" ? "Resend" : "SMTP";
        setPageNotice({ type: "success", text: `Convite enviado por e-mail via ${provider}.` });
      } else if (payload.auto_sent) {
        setPageNotice({ type: "success", text: "Convite enviado automaticamente via WhatsApp." });
      } else {
        setPageNotice({ type: "success", text: "Link de WhatsApp gerado. Abrindo para envio manual..." });
        if (payload.whatsapp_link) {
          window.open(String(payload.whatsapp_link), "_blank");
        }
      }
      await loadAnamnesisData();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao enviar convite." });
    }
  }

  async function handleResendAnamnesis(inviteId: number) {
    try {
      await api.post(`/api/anamnesis/invites/${inviteId}/resend`, {});
      setPageNotice({ type: "success", text: "Convite reenviado com sucesso." });
      await loadAnamnesisData();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao reenviar convite." });
    }
  }

  async function handleCancelAnamnesis(inviteId: number) {
    try {
      await api.post(`/api/anamnesis/invites/${inviteId}/cancel`, {});
      setPageNotice({ type: "success", text: "Convite cancelado com sucesso." });
      await loadAnamnesisData();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao cancelar convite." });
    }
  }

  async function handleReviewAnamnesis(responseId: number) {
    try {
      const response = await api.patch<AnamnesisResponse>(`/api/anamnesis/responses/${responseId}/review`, { status: "reviewed" });
      setPageNotice({ type: "success", text: "Resposta marcada como revisada." });
      await loadAnamnesisData();
      setSelectedAnamnesisResponse(response);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao revisar resposta." });
    }
  }

  async function copyToClipboard(text: string, successMessage: string) {
    try {
      await navigator.clipboard.writeText(text);
      setPageNotice({ type: "success", text: successMessage });
    } catch {
      setPageNotice({ type: "error", text: "Não foi possível copiar o link." });
    }
  }

  async function loadProgressEntries() {
    if (!evaluation) return;
    setTabLoading(true);
    try {
      const data = await api.get<ProgressEntry[]>(`/api/evaluations/${evaluation.id}/progress-entries`);
      setProgressEntries(data);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao carregar evolução." });
    } finally {
      setTabLoading(false);
    }
  }

  async function loadReports(selectFirst = false) {
    if (!evaluation) return;
    setTabLoading(true);
    try {
      const data = await api.get<ReportItem[]>(`/api/reports/?patient_id=${evaluation.patient_id}`);
      setReports(data);
      const preferredReport = data.find((item) => item.evaluation_id === evaluation.id) || data[0];
      if (selectFirst && preferredReport) {
        await openReport(preferredReport.id);
      }
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao carregar laudos." });
    } finally {
      setTabLoading(false);
    }
  }

  async function openReport(reportId: number) {
    try {
      const data = await api.get<ReportItem>(`/api/reports/${reportId}`);
      setSelectedReport(data);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao abrir laudo." });
    }
  }

  async function handleDocumentUpload() {
    if (!evaluation || documentRequiredMissing) return;
    setSavingDocument(true);
    try {
      const file = documentForm.file as File;
      const base64 = await new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result as string;
          resolve(result.split(",")[1]); // Remove data:mime;base64,
        };
        reader.readAsDataURL(file);
      });

      const payload = {
        evaluation_id: evaluation.id,
        patient_id: evaluation.patient_id,
        title: documentForm.title,
        document_type: documentForm.document_type,
        source: documentForm.source,
        document_date: documentForm.document_date || undefined,
        notes: documentForm.notes,
        is_relevant_for_report: documentForm.is_relevant_for_report,
        file_content: base64,
        file_name: file.name,
      };

      await api.post("/api/documents/add", payload);

      setPageNotice({ type: "success", text: "Documento enviado com sucesso." });
      setDocumentForm({ title: "", document_type: "other", source: "", document_date: "", notes: "", is_relevant_for_report: true, file: null });
      setShowDocumentForm(false);
      loadDocuments();
    } catch (err: any) {
      console.error("Upload error:", err);
      setPageNotice({ type: "error", text: err?.message || "Erro ao enviar documento." });
    } finally {
      setSavingDocument(false);
    }
  }

  async function handleDeleteDocument(documentId: number) {
    try {
      await api.delete(`/api/documents/delete/${documentId}`);
      setPageNotice({ type: "success", text: "Documento excluído com sucesso." });
      loadDocuments();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao excluir documento." });
    }
  }

  async function handleCreateProgress() {
    if (!evaluation || progressRequiredMissing) return;
    setSavingProgress(true);
    try {
      await api.post("/api/evaluations/progress-entries", {
        evaluation_id: evaluation.id,
        patient_id: evaluation.patient_id,
        entry_type: progressForm.entry_type,
        entry_date: progressForm.entry_date,
        start_time: progressForm.start_time || null,
        end_time: progressForm.end_time || null,
        objective: progressForm.objective,
        tests_applied: progressForm.tests_applied,
        observed_behavior: progressForm.observed_behavior,
        clinical_notes: progressForm.clinical_notes,
        next_steps: progressForm.next_steps,
        include_in_report: progressForm.include_in_report,
      });
      setPageNotice({ type: "success", text: "Registro de evolução salvo com sucesso." });
      setProgressForm({ entry_type: "anamnesis", entry_date: new Date().toISOString().slice(0, 10), start_time: "", end_time: "", objective: "", tests_applied: "", observed_behavior: "", clinical_notes: "", next_steps: "", include_in_report: true });
      setShowProgressForm(false);
      loadProgressEntries();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao salvar evolução." });
    } finally {
      setSavingProgress(false);
    }
  }

  async function handleDeleteProgress(entryId: number) {
    try {
      await api.delete(`/api/evaluations/progress-entries/${entryId}`);
      setPageNotice({ type: "success", text: "Registro de evolução excluído com sucesso." });
      loadProgressEntries();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao excluir evolução." });
    }
  }

  async function handleCreateReport() {
    if (!evaluation || reportRequiredMissing) return;
    setSavingReport(true);
    try {
      const report = await api.post<ReportItem>("/api/reports/", {
        evaluation_id: evaluation.id,
        patient_id: evaluation.patient_id,
        title: reportForm.title,
        interested_party: reportForm.interested_party,
        purpose: reportForm.purpose,
      });
      setPageNotice({ type: "success", text: "Laudo criado com sucesso." });
      setReportForm({ title: "", interested_party: "", purpose: "" });
      setShowReportForm(false);
      await loadReports();
      await openReport(report.id);
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao criar laudo." });
    } finally {
      setSavingReport(false);
    }
  }

  async function handleBuildReport(reportId: number) {
    try {
      const report = await api.post<ReportItem>(`/api/reports/${reportId}/build`, {});
      setSelectedReport(report);
      setPageNotice({ type: "success", text: "Seções do laudo regeneradas com sucesso." });
      loadReports();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao gerar laudo." });
    }
  }

  function handleOpenDeleteReportDialog(reportId: number) {
    setDeleteReportId(reportId);
    setDeleteReportConfirmationOpen(true);
  }

  function handleCloseDeleteReportDialog() {
    setDeleteReportId(null);
    setDeleteReportConfirmationOpen(false);
  }

  async function handleDeleteReport() {
    if (!deleteReportId) return;

    try {
      setDeletingReport(true);
      await api.delete(`/api/reports/${deleteReportId}`);
      setPageNotice({ type: "success", text: "Laudo excluído com sucesso." });
      if (selectedReport?.id === deleteReportId) {
        setSelectedReport(null);
      }
      handleCloseDeleteReportDialog();
      loadReports();
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao excluir laudo." });
    } finally {
      setDeletingReport(false);
    }
  }

  async function handleSaveSection(sectionId: number, editedText: string) {
    try {
      const updated = await api.patch<ReportSection>(`/api/reports/sections/${sectionId}`, { edited_text: editedText });
      if (selectedReport?.sections) {
        setSelectedReport({
          ...selectedReport,
          sections: selectedReport.sections.map((section) => section.id === sectionId ? { ...section, ...updated } : section),
        });
      }
      setPageNotice({ type: "success", text: "Seção salva com sucesso." });
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao salvar seção." });
    }
  }

  function openAddTestModal() {
    setSelectedInstrumentIds([]);
    setInstrumentFilterError(null);
    setShowAddTestModal(true);
    if (instruments.length === 0) {
      loadInstruments();
    }
  }

  function closeAddTestModal() {
    setShowAddTestModal(false);
    setSelectedInstrumentIds([]);
    setInstrumentFilterError(null);
  }

  function getTestUrl(instrumentCode: string, testId: number): string {
    // Normalize code (replace hyphens with underscores)
    const normalizedCode = instrumentCode.replace(/-/g, '_');
    
    const baseUrls: Record<string, string> = {
      "bfp": "/dashboard/tests/bfp",
      "fdt": "/dashboard/tests/fdt",
      "wasi": "/dashboard/tests/wasi",
      "wisc4": "/dashboard/tests/wisc4",
      "wais3": "/dashboard/tests/wais3",
      "bpa2": "/dashboard/tests/bpa2",
      "bai": "/dashboard/tests/bai",
      "ebadep_a": "/dashboard/tests/ebadep-a",
      "ebadep_ij": "/dashboard/tests/ebadep-ij",
      "ebaped_ij": "/dashboard/tests/ebadep-ij",
      "epq_j": "/dashboard/tests/epq-j",
      "etdah_ad": "/dashboard/tests/etdah-ad",
      "etdah_pais": "/dashboard/tests/etdah-pais",
      "ravlt": "/dashboard/tests/ravlt",
      "srs2": "/dashboard/tests/srs2",
      "scared": "/dashboard/tests/scared",
      "cars2_hf": "/dashboard/tests/cars2-hf",
      "mchat": "/dashboard/tests/mchat",
    };
    
    return `${baseUrls[normalizedCode] || "/dashboard/tests"}?evaluation_id=${evaluation?.id}&application_id=${testId}`;
  }

  async function removeTest(applicationId: number) {
    if (!evaluation) return;
    try {
      await api.delete(`/api/tests/applications/${applicationId}`);
      setEvaluation({
        ...evaluation,
        tests: evaluation.tests.filter((test) => test.id !== applicationId),
      });
      setPageNotice({ type: "success", text: "Teste removido com sucesso." });
    } catch (err: any) {
      setPageNotice({ type: "error", text: err?.message || "Erro ao remover teste." });
    }
  }

  function resolveReferenceDate() {
    return evaluation?.start_date || evaluation?.end_date || null;
  }

  function getPatientAge(birthDate: string | null, referenceDate?: string | null) {
    if (!birthDate) return "—";
    const birth = new Date(birthDate);
    const baseDate = referenceDate ? new Date(referenceDate) : new Date();
    if (isNaN(birth.getTime())) return "—";
    if (isNaN(baseDate.getTime())) return "—";

    let years = baseDate.getFullYear() - birth.getFullYear();
    let months = baseDate.getMonth() - birth.getMonth();

    if (baseDate.getDate() < birth.getDate()) {
      months -= 1;
    }

    if (months < 0) {
      years -= 1;
      months += 12;
    }

    if (years <= 0) {
      return `${months} ${months === 1 ? "mês" : "meses"}`;
    }

    if (months === 0) {
      return `${years} ${years === 1 ? "ano" : "anos"}`;
    }

    return `${years} ${years === 1 ? "ano" : "anos"} e ${months} ${months === 1 ? "mês" : "meses"}`;
  }

  function getPatientAgeNumber(birthDate: string | null, referenceDate?: string | null) {
    if (!birthDate) return null;
    const birth = new Date(birthDate);
    const baseDate = referenceDate ? new Date(referenceDate) : new Date();
    if (isNaN(birth.getTime()) || isNaN(baseDate.getTime())) return null;
    let age = baseDate.getFullYear() - birth.getFullYear();
    const monthDiff = baseDate.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && baseDate.getDate() < birth.getDate())) {
      age -= 1;
    }
    return age;
  }

  function formatDisplayDate(value: string | null | undefined) {
    if (!value) return "—";
    if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      const [year, month, day] = value.split("-");
      return `${day}/${month}/${year}`;
    }
    const date = new Date(value);
    if (isNaN(date.getTime())) return "—";
    return date.toLocaleDateString("pt-BR");
  }

  function getInstrumentAgeRestriction(instrumentCode: string) {
    const age = getPatientAgeNumber(evaluation?.patient_birth_date || null, resolveReferenceDate());
    if (age === null) return null;
    const rule = instruments.find((instrument) => instrument.code === instrumentCode);
    if (!rule) return null;
    if ((rule.min_age != null) && age < rule.min_age) return rule.age_message || null;
    if ((rule.max_age != null) && age > rule.max_age) return rule.age_message || null;
    return null;
  }

  function getInstrumentAgeRangeLabel(instrumentCode: string) {
    const rule = instruments.find((instrument) => instrument.code === instrumentCode);
    if (!rule || (rule.min_age == null && rule.max_age == null)) return "Faixa etária não definida";
    if (rule.min_age != null && rule.max_age != null) return `${rule.min_age} a ${rule.max_age} anos`;
    if (rule.min_age != null) return `${rule.min_age}+ anos`;
    if (rule.max_age != null) return `Até ${rule.max_age} anos`;
    return "Faixa etária não definida";
  }

  function getTestDisplayName(test: TestApp) {
    if (test.instrument_code !== "scared") {
      return test.instrument_name;
    }

    const classifiedForm = typeof test.classified_payload?.form_type === "string"
      ? test.classified_payload.form_type
      : null;
    const rawForm = typeof test.raw_payload?.form === "string"
      ? test.raw_payload.form
      : null;
    const form = classifiedForm || rawForm;

    if (form === "parent") {
      return "SCARED - Pais/Cuidadores";
    }

    if (form === "child") {
      return "SCARED - Autorrelato";
    }

    return test.instrument_name;
  }

  if (loading) {
    return (
      <PageContainer>
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-100 border-t-primary"></div>
          <p className="text-sm font-bold text-slate-400 uppercase tracking-widest animate-pulse">Sincronizando Dados Clínicos...</p>
        </div>
      </PageContainer>
    );
  }

  if (!evaluation) {
    return (
      <PageContainer>
        <EmptyState 
          title="Avaliação não encontrada" 
          description={errorMessage || "O registro solicitado pode ter sido arquivado ou removido."}
          icon={<AlertCircle className="h-12 w-12 text-slate-200" />}
          action={
            <Link href="/dashboard/evaluations">
              <Button variant="outline" className="gap-2 font-bold">
                <ArrowLeft className="h-4 w-4" />
                Voltar para Lista
              </Button>
            </Link>
          }
        />
      </PageContainer>
    );
  }

  const tabs = [
    { id: "overview" as TabType, label: "Visão Geral", icon: User },
    { id: "tests" as TabType, label: "Testes", icon: ClipboardList },
    { id: "anamnesis" as TabType, label: "Anamnese", icon: Send },
    { id: "documents" as TabType, label: "Documentos", icon: FolderOpen },
    { id: "evolution" as TabType, label: "Evolução", icon: StickyNote },
    { id: "report" as TabType, label: "Laudo", icon: FileText },
  ];
  const deadlineMeta = getEvaluationDeadlineMeta(evaluation.end_date, evaluation.status);

  const getTestesDisponiveis = () => {
    const codes = evaluation.tests.map(t => t.instrument_code);
    const disponiveis = instruments
      .map(i => ({
        code: i.code,
        name: i.name,
        id: i.id,
        ageRestriction: getInstrumentAgeRestriction(i.code),
      }))
      .filter(t => !codes.includes(t.code));

    return disponiveis.sort((a, b) => {
      const aBlocked = !!a.ageRestriction;
      const bBlocked = !!b.ageRestriction;
      if (aBlocked !== bBlocked) return aBlocked ? 1 : -1;
      return a.name.localeCompare(b.name);
    });
  };

  function toggleInstrumentSelection(instrumentId: number) {
    setSelectedInstrumentIds((current) =>
      current.includes(instrumentId)
        ? current.filter((id) => id !== instrumentId)
        : [...current, instrumentId]
    );
  }

  async function addSelectedTests() {
    if (!evaluation || selectedInstrumentIds.length === 0) return;
    setAddingTest(true);
    try {
      setInstrumentFilterError(null);
      const newTests = [];
      for (const instrumentId of selectedInstrumentIds) {
        const newTest = await api.post<any>("/api/tests/applications", {
          evaluation_id: evaluation.id,
          instrument_id: instrumentId,
        });
        newTests.push({
          id: newTest.id,
          instrument_name: newTest.instrument_name,
          instrument_code: newTest.instrument_code,
          applied_on: newTest.applied_on,
          is_validated: newTest.is_validated,
          status: newTest.is_validated ? "Concluído" : "Pendente",
        });
      }
      setEvaluation({
        ...evaluation,
        tests: [...evaluation.tests, ...newTests],
      });
      closeAddTestModal();
      setPageNotice({
        type: "success",
        text:
          newTests.length === 1
            ? "Teste adicionado com sucesso."
            : `${newTests.length} testes adicionados com sucesso.`,
      });
    } catch (err: any) {
      console.error("Erro ao adicionar testes:", err);
      setInstrumentFilterError(err?.message || "Erro ao adicionar testes.");
    } finally {
      setAddingTest(false);
    }
  }

  if (showAddTestModal) {
    const availableTests = getTestesDisponiveis();
    const selectedCount = selectedInstrumentIds.length;
    return (
      <div className="min-h-screen bg-slate-300 p-6 md:p-10">
        <div className="mx-auto max-w-7xl rounded-[36px] bg-[#f3f0e4] p-5 shadow-2xl ring-1 ring-black/5 md:p-7">
          <div className="rounded-[28px] bg-gradient-to-r from-[#f6f4ed] via-[#f2efe4] to-[#efe7bf] p-5 md:p-6">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-2xl font-medium">Adicionar Teste</h1>
              <Button variant="ghost" size="icon" onClick={closeAddTestModal}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            
            <p className="text-zinc-600 mb-4">Selecione os testes que deseja adicionar e confirme o envio em lote.</p>
            <div className="mb-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600">
              Idade do paciente: <span className="font-semibold text-slate-900">{getPatientAge(evaluation.patient_birth_date, resolveReferenceDate())}</span>
            </div>
            {instrumentFilterError && (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {instrumentFilterError}
              </div>
            )}
            
            {loadingInstruments ? (
              <div className="text-center py-8">
                <p className="text-zinc-500">Carregando instrumentos...</p>
              </div>
            ) : instruments.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <p>Nenhum instrumento foi cadastrado no sistema.</p>
              </div>
            ) : availableTests.length === 0 ? (
              <div className="text-center py-8 text-zinc-500">
                <p>Todos os testes disponíveis já foram adicionados.</p>
              </div>
            ) : (
              <>
                <div className="mb-4 rounded-xl border border-primary/10 bg-primary/5 px-4 py-3 text-sm text-slate-700">
                  <span className="font-semibold text-slate-900">{selectedCount}</span> teste(s) selecionado(s)
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {availableTests.map((test) => {
                  const ageRestriction = test.ageRestriction
                  const isSelected = selectedInstrumentIds.includes(test.id)
                  return (
                    <button
                      key={test.id}
                      type="button"
                      onClick={() => !ageRestriction && toggleInstrumentSelection(test.id)}
                      disabled={addingTest || !!ageRestriction}
                      className={`p-4 text-left rounded-xl border transition disabled:opacity-60 ${ageRestriction ? "border-rose-200 bg-rose-50" : isSelected ? "border-primary bg-primary/5" : "border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300"}`}
                    >
                      <div className="mb-3 flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium">{test.name}</p>
                          <p className="text-sm text-zinc-500">{test.code}</p>
                        </div>
                        <div className={`mt-0.5 flex h-5 w-5 items-center justify-center rounded border ${isSelected ? "border-primary bg-primary text-white" : "border-slate-300 bg-white"}`}>
                          {isSelected ? "✓" : ""}
                        </div>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">Faixa etária: {getInstrumentAgeRangeLabel(test.code)}</p>
                      {ageRestriction && <p className="mt-2 text-xs text-rose-700">{ageRestriction}</p>}
                    </button>
                  )
                })}
                </div>
              </>
            )}
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="ghost" className="font-bold text-slate-400" onClick={closeAddTestModal}>
                Cancelar
              </Button>
              <Button className="font-bold px-8 shadow-spike border-none" disabled={addingTest || selectedCount === 0} onClick={addSelectedTests}>
                {addingTest ? "Adicionando..." : `Adicionar selecionados${selectedCount > 0 ? ` (${selectedCount})` : ""}`}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <PageContainer>
      <PageHeader
        title={evaluation.code}
        breadcrumbs={
          <Link href="/dashboard/evaluations" className="inline-flex items-center text-xs font-bold text-primary uppercase tracking-widest hover:underline gap-1">
            <ArrowLeft className="h-3 w-3" />
            Processos de Avaliação
          </Link>
        }
        subtitle={`${evaluation.patient_name} • ${evaluation.status_display}`}
        actions={
          <div className="flex gap-3">
            <Button variant="outline" className="gap-2 border-slate-100 font-bold hover:bg-slate-50 transition-all" onClick={() => router.push(`/dashboard/evaluations/${evaluation.id}/edit`)}>
              <Edit className="h-4 w-4 text-slate-400" />
              Editar Processo
            </Button>
            <Button className="gap-2 shadow-spike font-bold" onClick={() => navigateToTab("report")}>
              <FileText className="h-4 w-4" />
              Gerar Laudo
            </Button>
          </div>
        }
      />

      <div className="flex flex-wrap gap-1 mb-8 bg-slate-100/50 p-1 rounded-xl border border-slate-100">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => navigateToTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2.5 text-[10px] font-black uppercase tracking-widest rounded-lg transition-all ${
              activeTab === tab.id
                ? "bg-white text-primary shadow-sm"
                : "text-slate-400 hover:text-slate-600 hover:bg-white/50"
            }`}
          >
            <tab.icon className="h-3.5 w-3.5" />
            {tab.label}
          </button>
        ))}
      </div>

          {pageNotice && (
            <div className={`mb-6 rounded-2xl px-4 py-3 text-sm ${pageNotice.type === "success" ? "border border-emerald-200 bg-emerald-50 text-emerald-800" : "border border-rose-200 bg-rose-50 text-rose-800"}`}>
              <div className="flex items-center justify-between gap-4">
                <span>{pageNotice.text}</span>
                <button onClick={() => setPageNotice(null)} className="text-xs font-medium opacity-80 hover:opacity-100">Fechar</button>
              </div>
            </div>
          )}

          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-in fade-in duration-500">
              <div className="lg:col-span-2 space-y-8">
                <SectionCard title="Dados Principais" description="Informações básicas e identificação do processo.">
                  <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    <InfoCard label="Paciente" value={evaluation.patient_name || "—"} icon={User} />
                    <InfoCard label="Idade de Referência" value={getPatientAge(evaluation.patient_birth_date, resolveReferenceDate())} icon={Calendar} />
                    <InfoCard label="Responsável" value={evaluation.patient_responsible_name || evaluation.examiner_name || "—"} icon={User} />
                    <InfoCard label="Data de Início" value={formatDisplayDate(evaluation.start_date)} icon={Calendar} />
                    <InfoCard label="Previsão de Conclusão" value={formatDisplayDate(evaluation.end_date)} icon={Clock} />
                    <InfoCard label="Status Atual" value={evaluation.status_display} icon={ShieldCheck} />
                  </div>

                  <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50/80 p-4">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className={`rounded-full border px-3 py-1 text-[10px] font-black uppercase tracking-widest ${deadlineMeta.badgeClassName}`}>
                        {deadlineMeta.label}
                      </span>
                      <span className="text-sm font-bold text-slate-500">{deadlineMeta.helperText}</span>
                    </div>
                  </div>

                  <div className="mt-8 space-y-6 pt-8 border-t border-slate-50">
                    {evaluation.title && (
                      <div>
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Título do Caso</h4>
                        <p className="text-sm font-bold text-slate-700">{evaluation.title}</p>
                      </div>
                    )}

                    {evaluation.referral_reason && (
                      <div>
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Motivo do Encaminhamento</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">{evaluation.referral_reason}</p>
                      </div>
                    )}

                    {evaluation.evaluation_purpose && (
                      <div>
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Finalidade</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">{evaluation.evaluation_purpose}</p>
                      </div>
                    )}
                  </div>
                </SectionCard>

                <SectionCard title="Observações e Hipóteses" description="Notas clínicas preliminares.">
                  <div className="space-y-6">
                    {evaluation.clinical_hypothesis ? (
                      <div>
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Hipótese Clínica</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">{evaluation.clinical_hypothesis}</p>
                      </div>
                    ) : (
                      <p className="text-xs font-bold text-slate-400 italic">Nenhuma hipótese clínica registrada.</p>
                    )}

                    {evaluation.general_notes && (
                      <div>
                        <h4 className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Anotações Gerais</h4>
                        <p className="text-sm text-slate-600 leading-relaxed">{evaluation.general_notes}</p>
                      </div>
                    )}
                  </div>
                </SectionCard>
              </div>

              <div className="space-y-8">
                <SectionCard title="Checklist Clínico" description="Progresso para o laudo.">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full ${evaluation.clinical_checklist?.anamnesis_completed ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <span className="text-xs font-bold text-slate-600">Anamnese</span>
                      </div>
                      <span className="text-[10px] font-black uppercase text-slate-400">{evaluation.clinical_checklist?.anamnesis_completed ? 'Completa' : 'Pendente'}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full ${evaluation.clinical_checklist?.has_validated_tests ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <span className="text-xs font-bold text-slate-600">Testagem</span>
                      </div>
                      <span className="text-[10px] font-black uppercase text-slate-400">{evaluation.clinical_checklist?.has_validated_tests ? 'Validada' : 'Em curso'}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                      <div className="flex items-center gap-3">
                        <div className={`h-2 w-2 rounded-full ${evaluation.clinical_checklist?.ready_for_report ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                        <span className="text-xs font-bold text-slate-600">Laudo Final</span>
                      </div>
                      <span className="text-[10px] font-black uppercase text-slate-400">{evaluation.clinical_checklist?.ready_for_report ? 'Pronto' : 'Aguardando'}</span>
                    </div>
                  </div>
                  <Button className="w-full mt-6 font-bold shadow-sm" onClick={() => navigateToTab("report")}>
                    Visualizar Laudo
                  </Button>
                </SectionCard>

                <SectionCard title="Ações Rápidas">
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full justify-between gap-3 border-slate-100 font-bold hover:bg-slate-50 group" onClick={openAddTestModal}>
                      <div className="flex items-center gap-3">
                        <Plus className="h-4 w-4 text-primary" />
                        <span>Adicionar Teste</span>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-primary transition-colors" />
                    </Button>
                    <Button variant="outline" className="w-full justify-between gap-3 border-slate-100 font-bold hover:bg-slate-50 group" onClick={() => navigateToTab("anamnesis")}>
                      <div className="flex items-center gap-3">
                        <Send className="h-4 w-4 text-emerald-500" />
                        <span>Enviar Anamnese</span>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-300 group-hover:text-primary transition-colors" />
                    </Button>
                  </div>
                </SectionCard>
              </div>
            </div>
          )}

          {activeTab === "tests" && (
            <div className="space-y-8">
              <SectionCard 
                title="Testes Aplicados" 
                description="Gerenciamento de instrumentos e baterias de testagem."
                actions={
                  <Button className="gap-2 font-bold shadow-sm" onClick={openAddTestModal}>
                    <Plus className="h-4 w-4" />
                    Adicionar Instrumento
                  </Button>
                }
              >
                {evaluation.tests.length === 0 ? (
                  <EmptyState
                    title="Nenhum teste aplicado"
                    description="Adicione instrumentos psicométricos para iniciar a coleta de dados."
                    icon={<ClipboardList className="h-10 w-10 text-slate-200" />}
                  />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-100">
                          <th className="pb-4 text-left text-[10px] font-black uppercase tracking-widest text-slate-400">Instrumento</th>
                          <th className="pb-4 text-left text-[10px] font-black uppercase tracking-widest text-slate-400">Aplicação</th>
                          <th className="pb-4 text-left text-[10px] font-black uppercase tracking-widest text-slate-400">Status</th>
                          <th className="pb-4 text-right text-[10px] font-black uppercase tracking-widest text-slate-400">Ações</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evaluation.tests.map((test) => (
                          <tr key={test.id} className="group border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                            <td className="py-5 font-bold text-slate-900">{getTestDisplayName(test)}</td>
                            
                            <td className="py-5 text-sm text-slate-500 font-bold">
                              {test.applied_on ? new Date(test.applied_on).toLocaleDateString("pt-BR") : "Aguardando"}
                            </td>
                            <td className="py-5">
                              <TestWorkflowBadge status={test.status} statusDisplay={test.status_display} />
                            </td>
                            <td className="py-5 text-right">
                              <div className="flex justify-end gap-2">
                                <Button variant="ghost" size="sm" className="font-bold text-primary" onClick={() => router.push(getTestUrl(test.instrument_code, test.id))}>Abrir</Button>
                                <Button variant="ghost" size="sm" className="font-bold text-rose-500 hover:text-rose-600" onClick={() => removeTest(test.id)}>Remover</Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </SectionCard>

              {!loadingInstruments && instruments.length > 0 && (
                <SectionCard 
                  title="Instrumentos Disponíveis" 
                  description="Instrumentos que podem ser adicionados a esta avaliação."
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {instruments
                      .filter(i => !evaluation.tests.map(t => t.instrument_code).includes(i.code))
                      .map((instrument) => {
                        const ageRestriction = getInstrumentAgeRestriction(instrument.code);
                        return (
                          <div 
                            key={instrument.id}
                            className={`p-4 rounded-xl border transition-all ${
                              ageRestriction 
                                ? "border-rose-200 bg-rose-50" 
                                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm cursor-pointer"
                            }`}
                            onClick={() => !ageRestriction && addTest(instrument.id)}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div>
                                <p className="font-bold text-slate-900">{instrument.name}</p>
                                <p className="text-sm text-slate-500">{instrument.code}</p>
                              </div>
                              {ageRestriction && (
                                <AlertCircle className="h-5 w-5 text-rose-500 flex-shrink-0" />
                              )}
                            </div>
                            <p className="mt-2 text-xs text-slate-500">Faixa etária: {getInstrumentAgeRangeLabel(instrument.code)}</p>
                            {ageRestriction && (
                              <p className="mt-2 text-xs text-rose-700 font-medium">{ageRestriction}</p>
                            )}
                          </div>
                        );
                      })}
                  </div>
                </SectionCard>
              )}
            </div>
          )}

          {activeTab === "anamnesis" && (
            <div className="space-y-8 animate-in fade-in duration-500">
              <SectionCard 
                title="Gestão de Anamneses" 
                description="Envio de convites e acompanhamento de respostas dos responsáveis."
                actions={
                  <Button className="gap-2 font-bold shadow-sm" onClick={() => setShowAnamnesisInviteForm(!showAnamnesisInviteForm)}>
                    <Send className="h-4 w-4" />
                    Novo Convite
                  </Button>
                }
              >
                {showAnamnesisInviteForm && (
                  <div className="mb-8 p-6 rounded-2xl border border-primary/20 bg-primary/5 space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Template de Anamnese</label>
                        <select 
                          value={anamnesisForm.template_id} 
                          onChange={(e) => setAnamnesisForm({ ...anamnesisForm, template_id: e.target.value })}
                          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                        >
                          <option value="">Selecione um modelo...</option>
                          {anamnesisTemplates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Nome do Destinatário</label>
                        <input 
                          value={anamnesisForm.recipient_name}
                          onChange={(e) => setAnamnesisForm({ ...anamnesisForm, recipient_name: e.target.value })}
                          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                          placeholder="Ex: Maria (Mãe)"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">E-mail</label>
                        <input 
                          value={anamnesisForm.recipient_email}
                          onChange={(e) => setAnamnesisForm({ ...anamnesisForm, recipient_email: e.target.value })}
                          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                          placeholder="email@exemplo.com"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Telefone (WhatsApp)</label>
                        <input 
                          value={anamnesisForm.recipient_phone}
                          onChange={(e) => setAnamnesisForm({ ...anamnesisForm, recipient_phone: e.target.value })}
                          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                          placeholder="(00) 00000-0000"
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Enviar primeiro via</label>
                        <select 
                          value={anamnesisForm.channel}
                          onChange={(e) => setAnamnesisForm({ ...anamnesisForm, channel: e.target.value })}
                          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                        >
                          <option value="email">E-mail</option>
                          <option value="whatsapp">WhatsApp</option>
                        </select>
                      </div>
                    </div>
                    <div className="flex gap-3 justify-end">
                      <Button variant="ghost" className="font-bold text-slate-400" onClick={() => setShowAnamnesisInviteForm(false)}>Cancelar</Button>
                      <Button className="font-bold px-8 shadow-sm" onClick={handleCreateAnamnesisInvite} disabled={savingAnamnesisInvite}>
                        {savingAnamnesisInvite ? "Enviando..." : "Enviar Agora"}
                      </Button>
                    </div>
                  </div>
                )}

                {tabLoading ? (
                  <div className="py-20 text-center animate-pulse text-slate-300 font-bold uppercase tracking-widest text-xs">Atualizando Anamneses...</div>
                ) : (
                  <div className="space-y-12">
                    {anamnesisInvites.filter(i => i.status !== "canceled" && i.status !== "expired").length > 0 && (
                      <div>
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4 ml-1">Convites Ativos</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {anamnesisInvites.filter(i => i.status !== "canceled" && i.status !== "expired").map((invite) => (
                            <div key={invite.id} className="p-5 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:shadow-spike transition-all group">
                              <div className="flex justify-between items-start mb-3">
                                <div>
                                  <h5 className="font-bold text-slate-900">{invite.template_name}</h5>
                                  <p className="text-[10px] font-bold text-slate-400 mt-0.5">
                                    {invite.recipient_name} • {invite.channel === "email" ? invite.recipient_email : invite.recipient_phone}
                                  </p>
                                  {invite.delivery_payload?.provider && (
                                    <p className="text-[9px] font-bold text-slate-300 mt-1">
                                      via {invite.delivery_payload.provider === "resend" ? "Resend" : invite.delivery_payload.provider === "evolution" ? "WhatsApp API" : invite.delivery_payload.provider === "wa_me_link" ? "Link wa.me" : "SMTP"}
                                      {invite.delivery_payload.auto_sent === false && " (manual)"}
                                    </p>
                                  )}
                                </div>
                                <Badge className={`${STATUS_COLORS[invite.status]} rounded-full text-[9px] font-black uppercase tracking-widest`}>
                                  {invite.status}
                                </Badge>
                              </div>
                              <div className="flex gap-2 mt-4 pt-4 border-t border-slate-100/50 flex-wrap">
                                <Button variant="ghost" size="sm" className="h-8 text-[10px] font-bold text-slate-500 hover:bg-slate-100 gap-1" onClick={() => copyToClipboard(invite.public_url, "Link copiado!")}>
                                  <Copy className="h-3 w-3" /> Link
                                </Button>
                                {invite.recipient_email && (
                                  <Button variant="ghost" size="sm" className="h-8 text-[10px] font-bold text-blue-600 hover:bg-blue-50 gap-1" onClick={() => handleSendAnamnesis(invite.id, "email")}>
                                    <Mail className="h-3 w-3" /> E-mail
                                  </Button>
                                )}
                                {invite.recipient_phone && (
                                  <Button variant="ghost" size="sm" className="h-8 text-[10px] font-bold text-emerald-600 hover:bg-emerald-50 gap-1" onClick={() => handleSendAnamnesis(invite.id, "whatsapp")}>
                                    <MessageCircle className="h-3 w-3" /> WhatsApp
                                  </Button>
                                )}
                                <Button variant="ghost" size="sm" className="h-8 text-[10px] font-bold text-rose-500 hover:bg-rose-50 ml-auto" onClick={() => handleCancelAnamnesis(invite.id)}>Cancelar</Button>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div>
                      <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-4 ml-1">Respostas Recebidas</h4>
                      {anamnesisResponses.length === 0 ? (
                        <EmptyState 
                          title="Nenhuma resposta" 
                          description="Novas respostas aparecerão aqui assim que forem enviadas." 
                          icon={<Mail className="h-10 w-10 text-slate-200" />}
                        />
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {anamnesisResponses.map((res) => (
                            <div key={res.id} onClick={() => setSelectedAnamnesisResponse(res)} className={`p-5 rounded-2xl border transition-all cursor-pointer ${selectedAnamnesisResponse?.id === res.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-slate-100 bg-white hover:border-slate-300'}`}>
                              <h5 className="font-bold text-slate-900">{res.template_name}</h5>
                              <p className="text-[10px] font-bold text-slate-400 mt-0.5">{res.submitted_by_name} ({res.submitted_by_relation})</p>
                              <div className="mt-3 flex items-center justify-between">
                                <span className="text-[10px] font-black uppercase tracking-widest text-slate-300">Recebido em {new Date(res.submitted_at || "").toLocaleDateString("pt-BR")}</span>
                                <Badge className={`${res.status === "reviewed" ? "bg-emerald-500" : "bg-primary"} text-white border-none rounded-full h-2 w-2 p-0`} />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {selectedAnamnesisResponse && (
                      <div className="pt-8 border-t border-slate-100 animate-in slide-in-from-bottom-4 duration-500">
                        <div className="flex items-center justify-between mb-6">
                          <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Conteúdo do Resumo</h4>
                          {selectedAnamnesisResponse.status !== "reviewed" && (
                            <Button size="sm" className="gap-2 font-bold shadow-sm" onClick={() => handleReviewAnamnesis(selectedAnamnesisResponse.id)}>
                              <CheckCircle2 className="h-4 w-4" />
                              Marcar como Revisada
                            </Button>
                          )}
                        </div>
                        <div className="print-area">
                          <AnamnesisResponseViewer
                            answers={selectedAnamnesisResponse.answers_payload}
                            template={anamnesisTemplates.find(t => t.id === selectedAnamnesisResponse.template_id || t.name === selectedAnamnesisResponse.template_name) as any}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </SectionCard>
            </div>
          )}

          {activeTab === "documents" && (
            <SectionCard 
              title="Arquivo de Documentos" 
              description="Upload e gestão de anexos clínicos, relatórios externos e exames."
              actions={
                <Button className="gap-2 font-bold shadow-sm" onClick={() => setShowDocumentForm(!showDocumentForm)}>
                  <Plus className="h-4 w-4" />
                  Upload
                </Button>
              }
            >
              {showDocumentForm && (
                <div className="mb-8 p-6 rounded-2xl border border-primary/20 bg-primary/5 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Título do Documento *</label>
                      <input 
                        value={documentForm.title}
                        onChange={(e) => setDocumentForm({ ...documentForm, title: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                        placeholder="Ex: Relatório Médico Dr. Smith"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Categoria</label>
                      <select 
                        value={documentForm.document_type}
                        onChange={(e) => setDocumentForm({ ...documentForm, document_type: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                      >
                        <option value="referral">Encaminhamento</option>
                        <option value="school_report">Escolar</option>
                        <option value="medical_report">Médico</option>
                        <option value="other">Outro</option>
                      </select>
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Selecionar Arquivo *</label>
                      <input 
                        type="file"
                        onChange={(e) => setDocumentForm({ ...documentForm, file: e.target.files?.[0] || null })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all file:mr-4 file:py-1 file:px-4 file:rounded-full file:border-0 file:text-[10px] file:font-black file:uppercase file:bg-primary/10 file:text-primary"
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 justify-end pt-2">
                    <Button variant="ghost" className="font-bold text-slate-400" onClick={() => setShowDocumentForm(false)}>Cancelar</Button>
                    <Button className="font-bold px-8 shadow-sm" onClick={handleDocumentUpload} disabled={savingDocument || !documentForm.file}>
                      {savingDocument ? "Salvando..." : "Fazer Upload"}
                    </Button>
                  </div>
                </div>
              )}

              {documents.length === 0 ? (
                <EmptyState title="Sem documentos" description="Ficou pendente o anexo de documentos para este paciente." icon={<FolderOpen className="h-10 w-10 text-slate-200" />} />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {documents.map((doc: any) => (
                    <div key={doc.id} className="p-4 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:shadow-spike transition-all group">
                      <div className="flex items-center gap-4">
                        <div className="h-10 w-10 rounded-xl bg-primary/5 flex items-center justify-center text-primary group-hover:bg-primary group-hover:text-white transition-colors">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h5 className="font-bold text-slate-900 truncate">{doc.title}</h5>
                          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 truncate">{doc.document_type}</p>
                        </div>
                      </div>
                      <div className="mt-4 flex gap-2">
                        <a href={resolveApiUrl(doc.file_url)} target="_blank" rel="noreferrer" className="flex-1">
                          <Button variant="outline" className="w-full text-[10px] font-black uppercase tracking-widest border-slate-100 h-8">Abrir</Button>
                        </a>
                        <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-slate-300 hover:text-rose-500" onClick={() => handleDeleteDocument(doc.id)}><X className="h-4 w-4" /></Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          )}

          {activeTab === "evolution" && (
            <SectionCard 
              title="Anotações de Evolução" 
              description="Registro diário das sessões avaliativas e observações clínicas."
              actions={
                <Button className="gap-2 font-bold shadow-sm" onClick={() => setShowProgressForm(!showProgressForm)}>
                  <Plus className="h-4 w-4" />
                  Nova Entrada
                </Button>
              }
            >
               {showProgressForm && (
                <div className="mb-8 p-6 rounded-2xl border border-primary/20 bg-primary/5 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Tipo de Entrada *</label>
                      <select 
                        value={progressForm.entry_type}
                        onChange={(e) => setProgressForm({ ...progressForm, entry_type: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                      >
                        <option value="testing_session">Sessão de Testagem</option>
                        <option value="anamnesis">Sessão de Anamnese</option>
                        <option value="clinical_notes">Nota Clínica</option>
                        <option value="other">Outro</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Data *</label>
                      <input 
                        type="date"
                        value={progressForm.entry_date}
                        onChange={(e) => setProgressForm({ ...progressForm, entry_date: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                      />
                    </div>
                    <div className="space-y-2 md:col-span-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Conteúdo Clínico *</label>
                      <textarea 
                        value={progressForm.clinical_notes}
                        onChange={(e) => setProgressForm({ ...progressForm, clinical_notes: e.target.value })}
                        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-600 outline-none focus:ring-2 focus:ring-primary/20 transition-all min-h-[120px]"
                        placeholder="Descreva observações, comportamentos e progressos da sessão..."
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 justify-end pt-2">
                    <Button variant="ghost" className="font-bold text-slate-400" onClick={() => setShowProgressForm(false)}>Cancelar</Button>
                    <Button className="font-bold px-8 shadow-sm" onClick={handleCreateProgress} disabled={savingProgress || !progressForm.clinical_notes}>
                      {savingProgress ? "Salvando..." : "Salvar Registro"}
                    </Button>
                  </div>
                </div>
              )}

              {evaluation.progress_entries.length === 0 ? (
                <EmptyState title="Sem registros" description="Documente o dia a dia da avaliação para compor o laudo." icon={<StickyNote className="h-10 w-10 text-slate-200" />} />
              ) : (
                <div className="space-y-6 relative ml-4 before:absolute before:left-[-16px] before:top-2 before:bottom-2 before:w-px before:bg-slate-100">
                  {evaluation.progress_entries.map((entry: any) => (
                    <div key={entry.id} className="relative group">
                      <div className="absolute left-[-20px] top-2 h-2 w-2 rounded-full bg-slate-200 group-hover:bg-primary transition-colors" />
                      <div className="p-6 rounded-2xl border border-slate-100 hover:border-slate-200 bg-white shadow-sm transition-all">
                        <div className="flex justify-between items-center mb-3">
                          <Badge variant="outline" className="text-[9px] font-black uppercase tracking-widest border-primary/20 text-primary">{entry.entry_type_display}</Badge>
                          <span className="text-[10px] font-bold text-slate-400">{new Date(entry.entry_date).toLocaleDateString("pt-BR")}</span>
                        </div>
                        <p className="text-sm font-medium text-slate-600 leading-relaxed">{entry.clinical_notes}</p>
                        <div className="mt-4 flex justify-end">
                          <Button variant="ghost" size="sm" className="h-8 text-[10px] font-bold text-rose-500 hover:bg-rose-50" onClick={() => handleDeleteProgress(entry.id)}>Remover</Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          )}

          {activeTab === "report" && (
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8 animate-in fade-in duration-700">
              <SectionCard title="Criação e Gestão de Laudo" description="Composição técnica do documento final de avaliação.">
                {reports.length === 0 ? (
                  <div className="py-12 flex flex-col items-center justify-center text-center space-y-6">
                    <div className="h-16 w-16 rounded-full bg-slate-50 flex items-center justify-center">
                      <FileText className="h-8 w-8 text-slate-200" />
                    </div>
                    <div className="max-w-sm space-y-2">
                      <h4 className="font-bold text-slate-900">Preparado para Gerar o Laudo?</h4>
                      <p className="text-sm text-slate-500">O sistema consolidará testes validados e registros de anamnese automaticamente.</p>
                    </div>
                    <Button
                      size="lg"
                      className="px-10 font-bold shadow-spike"
                      onClick={() => router.push(`/dashboard/reports/generate/${evaluation.id}`)}
                    >
                      Criar Novo Laudo
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-8">
                     <div className="space-y-4">
                        {reports.map((r) => (
                          <div
                            key={r.id}
                            className={`p-4 rounded-xl border transition-all group ${selectedReport?.id === r.id ? 'border-primary/30 bg-primary/5' : 'border-slate-100 hover:border-primary/30 hover:bg-slate-50'}`}
                          >
                            <div className="flex items-center justify-between gap-4">
                              <button
                                type="button"
                                onClick={() => openReport(r.id)}
                                className="flex min-w-0 flex-1 items-center justify-between gap-4 text-left"
                              >
                                <div className="space-y-1 flex-1 min-w-0">
                                  <div className="flex items-center gap-2">
                                    <FileText className="h-4 w-4 text-primary" />
                                    <span className="text-sm font-bold text-slate-900">{r.evaluation_title || r.evaluation_code}</span>
                                    <Badge className={`${r.evaluation_id === evaluation.id ? 'bg-emerald-500' : 'bg-slate-500'} text-white border-none rounded-full px-2 py-0.5 text-[8px] font-black`}>
                                      {r.evaluation_id === evaluation.id ? 'Avaliação atual' : 'Outro laudo'}
                                    </Badge>
                                  </div>
                                  <div className="flex items-center gap-3 text-xs text-slate-500 flex-wrap">
                                    <span>Autor: {r.author_name}</span>
                                    <span className="h-1 w-1 rounded-full bg-slate-300" />
                                    <span>Criado em: {new Date(r.created_at).toLocaleDateString("pt-BR")}</span>
                                    <span className="h-1 w-1 rounded-full bg-slate-300" />
                                    <span className={`font-semibold ${r.status === 'finalized' ? 'text-emerald-600' : 'text-amber-600'}`}>
                                      {r.status === 'finalized' ? 'Finalizado' : 'Em andamento'}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-300 transition-colors group-hover:border-primary/20 group-hover:text-primary">
                                  <ChevronRight className="h-5 w-5" />
                                </div>
                              </button>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 shrink-0 rounded-full text-slate-400 hover:bg-red-50 hover:text-red-600"
                                onClick={() => handleOpenDeleteReportDialog(r.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                     </div>

                     {selectedReport && (
                        <div className="pt-8 border-t border-slate-100 animate-in slide-in-from-right-4 duration-500">
                          <div className="flex justify-between items-center mb-6">
                            <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Seções do Documento</h4>
                            <div className="flex gap-2">
                               <Button
                                 variant="outline"
                                 size="sm"
                                 className="font-bold gap-2 text-primary border-primary/20"
                                 onClick={() => router.push(`/dashboard/reports/${selectedReport.id}`)}
                               >
                                  <FileText className="h-4 w-4" /> Abrir Editor
                                </Button>
                            </div>
                          </div>
                          <div className="space-y-4">
                            {(selectedReport.sections || []).map((sec) => (
                              <div key={sec.id} className="p-6 rounded-2xl border border-slate-100 bg-white hover:border-slate-200 transition-all shadow-sm">
                                <div className="flex items-center justify-between mb-4">
                                  <h6 className="text-[11px] font-black uppercase tracking-widest text-slate-900">{sec.title}</h6>
                                  <Badge variant="outline" className="text-[8px] font-black uppercase border-slate-100">{sec.key}</Badge>
                                </div>
                                <textarea 
                                  defaultValue={sec.edited_text || sec.generated_text}
                                  onBlur={(e) => handleSaveSection(sec.id, e.target.value)}
                                  className="w-full text-sm text-slate-600 leading-relaxed bg-transparent border-none focus:ring-0 min-h-[100px] resize-none"
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                     )}
                  </div>
                )}
              </SectionCard>

              <div className="space-y-8">
                 <SectionCard title="Configurações">
                   <div className="space-y-6">
                      <div className="space-y-3">
                         <h5 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Paleta Clínica</h5>
                         <div className="flex gap-2">
                            <div className="h-6 w-6 rounded-full bg-primary" />
                            <div className="h-6 w-6 rounded-full bg-emerald-400" />
                            <div className="h-6 w-6 rounded-full bg-amber-400" />
                         </div>
                      </div>
                      <div className="pt-4 border-t border-slate-50">
                        <Button
                          className="w-full justify-start gap-3 h-12 bg-white text-slate-700 border border-slate-100 hover:bg-slate-50 font-bold"
                          onClick={() =>
                            selectedReport
                              ? router.push(`/dashboard/reports/${selectedReport.id}`)
                              : router.push(`/dashboard/reports/generate/${evaluation.id}`)
                          }
                        >
                           <Sparkles className="h-4 w-4 text-primary" /> Redigir com AI
                         </Button>
                      </div>
                   </div>
                 </SectionCard>
              </div>
        </div>
      )}

      {deleteReportConfirmationOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-8 shadow-xl">
            <div className="flex items-start gap-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-red-50">
                <AlertCircle className="h-6 w-6 text-red-500" />
              </div>
              <div className="flex-1 space-y-2">
                <h3 className="text-lg font-bold text-slate-900">Excluir Laudo?</h3>
                <p className="text-sm text-slate-600">
                  Esta ação irá remover permanentemente o laudo selecionado.
                </p>
                <p className="text-sm font-bold text-red-600">Esta ação não pode ser desfeita.</p>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <Button
                variant="outline"
                className="font-bold"
                onClick={handleCloseDeleteReportDialog}
                disabled={deletingReport}
              >
                Cancelar
              </Button>
              <Button
                variant="destructive"
                className="font-bold"
                onClick={handleDeleteReport}
                disabled={deletingReport}
              >
                {deletingReport ? (
                  <>
                    <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    Excluindo...
                  </>
                ) : (
                  <>
                    <Trash2 className="mr-2 h-4 w-4" />
                    Sim, Excluir
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {showAddTestModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="w-full max-w-lg bg-white rounded-[32px] shadow-spike border border-slate-100 overflow-hidden animate-in zoom-in-95 duration-300">
             <div className="p-8 border-b border-slate-50 bg-slate-50/50">
               <div className="flex justify-between items-center">
                  <h3 className="text-xl font-bold text-slate-900">Aplicar Instrumento</h3>
                  <button onClick={closeAddTestModal} className="p-2 rounded-full hover:bg-white text-slate-400 hover:text-slate-600 transition-all"><X className="h-5 w-5" /></button>
                </div>
                <p className="mt-1 text-sm text-slate-500">Selecione o teste psicométrico para compor o inventário.</p>
              </div>
              
              <div className="p-8 space-y-6">
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-slate-400">Selecione os testes</label>
                  <p className="text-sm text-slate-500">Use a grade acima para marcar os instrumentos e confirme no botão final.</p>
                  {instrumentFilterError && <p className="text-xs font-bold text-rose-500 mt-2">{instrumentFilterError}</p>}
                </div>

               <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-2xl border border-slate-100 bg-slate-50">
                     <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Aplicações</p>
                     <p className="text-xl font-bold text-slate-900">{evaluation.tests.length}</p>
                  </div>
                  <div className="p-4 rounded-2xl border border-slate-100 bg-slate-50">
                     <p className="text-[10px] font-black uppercase tracking-widest text-slate-400 mb-1">Favoritos</p>
                     <p className="text-xl font-bold text-slate-900">3</p>
                  </div>
               </div>
             </div>

              <div className="p-8 pt-4 bg-slate-50/50 flex justify-end gap-3">
                 <Button variant="ghost" className="font-bold text-slate-400" onClick={closeAddTestModal}>Cancelar</Button>
                 <Button className="font-bold px-8 shadow-spike border-none" disabled={addingTest || selectedInstrumentIds.length === 0} onClick={addSelectedTests}>
                    {addingTest ? "Adicionando..." : `Adicionar selecionados${selectedInstrumentIds.length > 0 ? ` (${selectedInstrumentIds.length})` : ""}`}
                 </Button>
              </div>
           </div>
        </div>
      )}
    </PageContainer>
  );
}
