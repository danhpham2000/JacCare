import type { ReactNode } from "react";
import { ArrowRight, Save } from "lucide-react";
import { COVERAGE_OPTIONS, INSURANCE_PROVIDERS } from "../lib/insurance";
import type { IntakePayload } from "../types/care";

type Props = {
  value: IntakePayload;
  loading: boolean;
  saving: boolean;
  onChange: (payload: IntakePayload) => void;
  onSubmit: () => void;
  onSave: () => void;
};

const LANGUAGE_OPTIONS = ["English", "Spanish", "Vietnamese"];
const TRANSPORT_OPTIONS = [
  { value: "public_transit", label: "Public transit" },
  { value: "no_car", label: "No car" },
  { value: "car", label: "Car" },
  { value: "phone", label: "Phone only" },
];
const URGENCY_OPTIONS = ["now", "today", "this week", "routine"];

export function IntakeForm({ value, loading, saving, onChange, onSubmit, onSave }: Props) {
  const update = <K extends keyof IntakePayload>(key: K, next: IntakePayload[K]) => onChange({ ...value, [key]: next });
  const providerOptions = INSURANCE_PROVIDERS[value.insurance_status] ?? INSURANCE_PROVIDERS.uninsured;
  const insuranceDisabled = value.insurance_status === "uninsured";

  return (
    <section className="rounded-[28px] border border-[#E6DDD1] bg-white p-6 shadow-[0_20px_70px_rgba(15,23,42,0.08)]">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">New request</p>
          <h2 className="mt-2 text-2xl font-semibold text-slate-950">Collect the care details</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
            Keep the request concrete. Coverage, timing, transport, and care need drive the route.
          </p>
        </div>
        <button
          className="focus-ring inline-flex items-center gap-2 rounded-full border border-[#D8C9B7] px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-[#FFF7ED] disabled:opacity-60"
          onClick={onSave}
          disabled={saving}
        >
          <Save className="h-4 w-4" />
          {saving ? "Saving..." : "Save profile"}
        </button>
      </div>

      <div className="mt-6 grid gap-6">
        <FormSection title="Coverage and payment" description="If you have coverage, add it here. If you do not, the route will prioritize self-pay and sliding-scale options.">
          <div className="grid gap-4 xl:grid-cols-2">
            <Select
              label="Coverage type"
              value={value.insurance_status}
              options={COVERAGE_OPTIONS.map((item) => ({ value: item.value, label: item.label }))}
              onChange={(next) => {
                const nextProvider = (INSURANCE_PROVIDERS[next] ?? [""])[0] ?? "";
                onChange({
                  ...value,
                  insurance_status: next,
                  insurance_provider: next === "uninsured" ? "" : nextProvider,
                  insurance_plan: next === "uninsured" ? "" : value.insurance_plan,
                  member_id: next === "uninsured" ? "" : value.member_id,
                });
              }}
            />
            <Select
              label="Coverage provider"
              value={value.insurance_provider}
              options={providerOptions.map((item) => ({ value: item === "No active coverage" ? "" : item, label: item }))}
              onChange={(next) => update("insurance_provider", next)}
              disabled={insuranceDisabled}
            />
            <Field
              label="Plan name"
              value={value.insurance_plan}
              placeholder="Silver 94 HMO"
              onChange={(next) => update("insurance_plan", next)}
              disabled={insuranceDisabled}
            />
            <Field
              label="Member ID (optional)"
              value={value.member_id}
              placeholder="Use the number on the card"
              onChange={(next) => update("member_id", next)}
              disabled={insuranceDisabled}
            />
          </div>
        </FormSection>

        <FormSection title="Care request" description="These constraints determine urgency, match quality, and affordability.">
          <div className="grid gap-4 xl:grid-cols-2">
            <Field label="ZIP code" value={value.zip_code} placeholder="78705" onChange={(next) => update("zip_code", next)} />
            <Select
              label="Urgency"
              value={value.urgency}
              options={URGENCY_OPTIONS.map((item) => ({ value: item, label: item }))}
              onChange={(next) => update("urgency", next)}
            />
            <Field label="Care need" value={value.care_need} placeholder="child fever" onChange={(next) => update("care_need", next)} />
            <Field
              label="Household situation"
              value={value.household}
              placeholder="single parent with one child"
              onChange={(next) => update("household", next)}
            />
          </div>
        </FormSection>

        <FormSection title="Access" description="Language, transport, and budget affect the route quality.">
          <div className="grid gap-4 xl:grid-cols-2">
            <Select
              label="Preferred language"
              value={value.language}
              options={LANGUAGE_OPTIONS.map((item) => ({ value: item, label: item }))}
              onChange={(next) => update("language", next)}
            />
            <Select
              label="Transport"
              value={value.transport_mode}
              options={TRANSPORT_OPTIONS}
              onChange={(next) => update("transport_mode", next)}
            />
            <label className="xl:col-span-2">
              <div className="flex items-center justify-between gap-3 text-sm font-medium text-slate-700">
                <span>Budget</span>
                <span className="rounded-full bg-[#FFF7ED] px-3 py-1 text-[#8F3D2E]">${value.budget}</span>
              </div>
              <input
                className="mt-3 w-full accent-[#B85C38]"
                type="range"
                min="0"
                max="400"
                step="5"
                value={value.budget}
                onChange={(event) => update("budget", Number(event.target.value))}
              />
            </label>
          </div>
        </FormSection>
      </div>

      <button
        className="focus-ring mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#B85C38] px-4 py-3 font-semibold text-white hover:bg-[#8F3D2E] disabled:cursor-not-allowed disabled:opacity-60"
        onClick={onSubmit}
        disabled={loading}
      >
        {loading ? "Running request..." : "Continue to safety check"}
        <ArrowRight className="h-4 w-4" />
      </button>
    </section>
  );
}

function FormSection({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[24px] border border-[#EEE7DD] bg-[#FCFAF7] p-4">
      <div className="mb-4">
        <p className="text-sm font-semibold text-slate-900">{title}</p>
        <p className="mt-1 text-sm text-slate-600">{description}</p>
      </div>
      {children}
    </section>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
  disabled = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <input
        className="focus-ring mt-1 w-full rounded-2xl border border-[#D8C9B7] bg-white px-4 py-3 disabled:bg-slate-50 disabled:text-slate-400"
        value={value}
        placeholder={placeholder}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
  disabled = false,
}: {
  label: string;
  value: string;
  options: Array<{ value: string; label: string }>;
  onChange: (value: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <select
        className="focus-ring mt-1 w-full rounded-2xl border border-[#D8C9B7] bg-white px-4 py-3 disabled:bg-slate-50 disabled:text-slate-400"
        value={value}
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <option key={`${label}-${option.value}-${option.label}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
