import { AlertTriangle, CheckCircle2 } from "lucide-react";

type Props = {
  level: string;
  message: string;
};

export function SafetyBanner({ level, message }: Props) {
  const emergency = level === "emergency";
  return (
    <div
      className={`flex gap-3 rounded-[24px] border p-4 shadow-[0_18px_50px_rgba(15,23,42,0.06)] ${
        emergency
          ? "border-[#F3B7B3] bg-[#FFF1EF] text-[#7F1D1D]"
          : "border-[#E9D3A8] bg-[#FFF7E8] text-slate-900"
      }`}
    >
      {emergency ? <AlertTriangle className="h-5 w-5 shrink-0" /> : <CheckCircle2 className="h-5 w-5 shrink-0" />}
      <div>
        <p className="text-sm font-semibold">{emergency ? "Emergency routing" : "Safety check"}</p>
        <p className="mt-1 text-sm leading-6">{message}</p>
      </div>
    </div>
  );
}
