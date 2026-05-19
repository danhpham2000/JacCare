import type { ReactNode } from "react";
import { BadgeDollarSign, Bus, Languages, MapPin, Phone, ShieldCheck } from "lucide-react";
import type { ClinicOption } from "../types/care";

type Props = {
  option: ClinicOption;
  title: string;
  highlight?: boolean;
};

const BREAKDOWN_LABELS: Record<string, string> = {
  cost_fit: "Cost fit",
  insurance_or_sliding_scale: "Coverage",
  distance: "Distance",
  transportation: "Transit",
  language: "Language",
  care_need: "Care match",
  documents: "Documents",
};

export function CareOptionCard({ option, title, highlight = false }: Props) {
  return (
    <article className={`rounded-[28px] border p-5 shadow-[0_20px_70px_rgba(15,23,42,0.08)] ${highlight ? "border-[#D9C2AE] bg-[#FFF9F2]" : "border-[#E6DDD1] bg-white"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#9A4E2D]">{title}</p>
          <h3 className="mt-2 text-2xl font-semibold leading-tight text-slate-900">{option.name}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600">{option.reason}</p>
        </div>
        <div className="min-w-[84px] rounded-[22px] bg-white px-3 py-3 text-center shadow-sm">
          <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Score</p>
          <p className="mt-1 text-2xl font-semibold text-[#0f766e]">{option.score}</p>
        </div>
      </div>

      <dl className="mt-5 grid gap-3 sm:grid-cols-2">
        <Metric icon={<BadgeDollarSign className="h-4 w-4" />} label="Estimated cost" value={option.estimated_cost} />
        <Metric icon={<MapPin className="h-4 w-4" />} label="Distance" value={option.distance} />
        <Metric icon={<Bus className="h-4 w-4" />} label="Transportation" value={option.transportation?.name ?? "Call to confirm"} />
        <Metric icon={<Languages className="h-4 w-4" />} label="Languages" value={option.languages.join(", ")} />
      </dl>

      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        {option.accepts_uninsured && (
          <span className="rounded-full bg-[#EAF7F4] px-3 py-1.5 font-medium text-[#0f766e]">Uninsured accepted</span>
        )}
        {option.sliding_scale && (
          <span className="rounded-full bg-[#FFF1DB] px-3 py-1.5 font-medium text-[#9A4E2D]">Sliding scale</span>
        )}
        <span className="rounded-full bg-[#F4F4F5] px-3 py-1.5 font-medium text-slate-700">{option.phone}</span>
      </div>

      {option.insurance_verification && (
        <div className="mt-4 rounded-[22px] border border-[#EEE7DD] bg-[#FCFAF7] p-4 text-sm leading-6 text-slate-700">
          <p className="font-semibold text-slate-900">Payment and coverage note</p>
          <p className="mt-1">{option.insurance_verification.message}</p>
        </div>
      )}

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {Object.entries(option.score_breakdown).map(([key, value]) => (
          <div key={key} className="rounded-2xl border border-[#EEE7DD] bg-white/80 p-3">
            <div className="flex items-center justify-between gap-3 text-sm">
              <span className="text-slate-600">{BREAKDOWN_LABELS[key] ?? key}</span>
              <span className="font-semibold text-slate-900">{value}</span>
            </div>
            <div className="mt-2 h-2 rounded-full bg-[#F2ECE4]">
              <div className="h-2 rounded-full bg-[#0f766e]" style={{ width: `${Math.max(8, Math.min(100, value))}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="mt-5 flex items-center justify-between gap-3 rounded-[22px] border border-[#EEE7DD] bg-white px-4 py-3 text-sm text-slate-700">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-4 w-4 text-[#0f766e]" />
          <span>Last updated {option.last_updated ?? "recently"}</span>
        </div>
        <a
          className="inline-flex items-center gap-2 font-semibold text-[#0f766e]"
          href={option.website}
          target="_blank"
          rel="noreferrer"
        >
          <Phone className="h-4 w-4" />
          Contact
        </a>
      </div>
    </article>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-[22px] border border-[#EEE7DD] bg-white/80 p-4">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 text-[#9A4E2D]">{icon}</span>
        <div>
          <dt className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</dt>
          <dd className="mt-1 text-sm font-medium leading-6 text-slate-900">{value}</dd>
        </div>
      </div>
    </div>
  );
}
