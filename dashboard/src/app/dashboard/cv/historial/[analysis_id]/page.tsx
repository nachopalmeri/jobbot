"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, FileText } from "lucide-react";

import { apiRequest } from "@/lib/api";

interface AnalysisDetail {
  id: number;
  type: string;
  has_job_match: boolean;
  prompt_tokens: number;
  response_tokens: number;
  total_tokens: number;
  created_at: string;
}

export default function AnalysisDetailPage() {
  const params = useParams<{ analysis_id: string }>();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiRequest<AnalysisDetail>(`/cv/history/${params.analysis_id}`, {}, true);
        setDetail(data);
      } catch (loadError) {
        setError(
          loadError && typeof loadError === "object" && "message" in loadError
            ? String(loadError.message)
            : "No se pudo cargar el detalle.",
        );
      }
    };

    void load();
  }, [params.analysis_id]);

  return (
    <div className="min-h-full bg-[linear-gradient(180deg,#f6f8fc_0%,#eef2f8_100%)] p-6">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          href="/dashboard/cv/historial"
          className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft size={16} />
          Volver al historial
        </Link>

        {error ? (
          <div className="rounded-[24px] border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
            {error}
          </div>
        ) : null}

        {detail ? (
          <section className="rounded-[30px] border border-slate-200 bg-white p-7 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
                <FileText size={20} />
              </div>
              <div>
                <h1 className="text-3xl font-semibold tracking-tight text-slate-950">
                  Análisis #{detail.id}
                </h1>
                <p className="mt-2 text-sm leading-7 text-slate-600">
                  Registro histórico de uso de la CV Suite. El backend actual conserva metadatos del
                  análisis para trazabilidad y consumo de IA.
                </p>
              </div>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm font-medium text-slate-500">Fecha</p>
                <p className="mt-2 text-xl font-semibold text-slate-950">
                  {new Date(detail.created_at).toLocaleString("es-AR")}
                </p>
              </div>
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm font-medium text-slate-500">Match con vacante</p>
                <p className="mt-2 text-xl font-semibold text-slate-950">
                  {detail.has_job_match ? "Sí" : "No"}
                </p>
              </div>
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm font-medium text-slate-500">Prompt tokens</p>
                <p className="mt-2 text-xl font-semibold text-slate-950">{detail.prompt_tokens || 0}</p>
              </div>
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-5">
                <p className="text-sm font-medium text-slate-500">Response tokens</p>
                <p className="mt-2 text-xl font-semibold text-slate-950">{detail.response_tokens || 0}</p>
              </div>
            </div>

            <div className="mt-4 rounded-[24px] border border-slate-200 bg-slate-950 p-5 text-white">
              <p className="text-sm font-medium text-slate-300">Consumo total</p>
              <p className="mt-2 text-3xl font-semibold">{detail.total_tokens || 0} tokens</p>
            </div>
          </section>
        ) : null}
      </div>
    </div>
  );
}
