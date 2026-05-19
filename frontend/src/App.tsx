import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowRight,
  BadgeDollarSign,
  ClipboardList,
  FileSearch,
  Languages,
  LogOut,
  MapPinned,
  Pill,
  ShieldAlert,
  UserRound,
} from "lucide-react";
import { CareMap } from "./components/CareMap";
import { CareOptionCard } from "./components/CareOptionCard";
import { GraphVisualizer } from "./components/GraphVisualizer";
import { IntakeForm } from "./components/IntakeForm";
import { SafetyBanner } from "./components/SafetyBanner";
import {
  fetchMe,
  loadHistory,
  login,
  logout,
  register,
  runCareRoute,
  saveProfile,
  setSessionToken,
  sessionToken,
} from "./lib/api";
import { COVERAGE_OPTIONS } from "./lib/insurance";
import type {
  AppUser,
  CarePlan,
  HistoryItem,
  IntakePayload,
  LiveEligibilitySource,
  LocalizedPlan,
} from "./types/care";

const EMPTY_PROFILE: IntakePayload = {
  zip_code: "",
  insurance_status: "uninsured",
  insurance_provider: "",
  insurance_plan: "",
  member_id: "",
  budget: 50,
  language: "English",
  transport_mode: "public_transit",
  care_need: "",
  urgency: "today",
  household: "",
};

type WorkspaceView = "new_request" | "profile" | "history";

export default function App() {
  const [user, setUser] = useState<AppUser | null>(null);
  const [payload, setPayload] = useState<IntakePayload>(EMPTY_PROFILE);
  const [plan, setPlan] = useState<CarePlan | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [language, setLanguage] = useState("English");
  const [activeView, setActiveView] = useState<WorkspaceView>("new_request");
  const [activeStep, setActiveStep] = useState(1);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authForm, setAuthForm] = useState({ full_name: "", email: "", password: "" });
  const [booting, setBooting] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [planLoading, setPlanLoading] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeContent: LocalizedPlan | null = useMemo(() => {
    if (!plan) {
      return null;
    }
    return plan.translations[language] ?? plan.translations.English ?? null;
  }, [plan, language]);

  useEffect(() => {
    const token = sessionToken();
    if (!token) {
      setBooting(false);
      return;
    }
    void hydrateSession();
  }, []);

  async function hydrateSession() {
    try {
      const currentUser = await fetchMe();
      setUser(currentUser);
      setPayload(currentUser.profile);
      setLanguage(currentUser.profile.language || "English");
      setHistory(await loadHistory());
    } catch {
      setSessionToken(null);
    } finally {
      setBooting(false);
    }
  }

  async function handleAuthSubmit() {
    setAuthLoading(true);
    setError(null);
    try {
      const session =
        authMode === "login"
          ? await login({ email: authForm.email, password: authForm.password })
          : await register(authForm);
      setSessionToken(session.token);
      setUser(session.user);
      setPayload(session.user.profile);
      setLanguage(session.user.profile.language || "English");
      setHistory(await loadHistory());
      setPlan(null);
      setActiveView("new_request");
      setActiveStep(1);
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to sign in");
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleSaveProfile() {
    setProfileSaving(true);
    setError(null);
    try {
      const saved = await saveProfile(payload);
      setPayload(saved);
      setLanguage(saved.language || "English");
      if (user) {
        setUser({ ...user, profile: saved });
      }
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to save profile");
    } finally {
      setProfileSaving(false);
    }
  }

  async function handleRunRoute() {
    setPlanLoading(true);
    setError(null);
    try {
      const result = await runCareRoute(payload);
      setPlan(result);
      setLanguage(payload.language || "English");
      setHistory(await loadHistory());
      setActiveView("new_request");
      setActiveStep(2);
      if (user) {
        setUser({ ...user, profile: payload });
      }
    } catch (event) {
      setError(event instanceof Error ? event.message : "Unable to run care route");
    } finally {
      setPlanLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await logout();
    } catch {
      // Local reset is enough if the session is already invalid.
    }
    setSessionToken(null);
    setUser(null);
    setPlan(null);
    setHistory([]);
    setPayload(EMPTY_PROFILE);
    setLanguage("English");
    setActiveView("new_request");
    setActiveStep(1);
  }

  function startNewRequest() {
    setPlan(null);
    setError(null);
    setActiveView("new_request");
    setActiveStep(1);
  }

  if (booting) {
    return (
      <main className="flex min-h-screen items-center justify-center px-6">
        <div className="rounded-full border border-[#D8C9B7] bg-white/90 px-5 py-3 text-sm text-slate-700 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
          Loading CareRoute...
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen">
        <section className="mx-auto grid min-h-screen max-w-6xl gap-10 px-6 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-[#E9D9C7] bg-white/75 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-[#B85C38]">
              <MapPinned className="h-4 w-4" />
              Care access planning
            </div>
            <h1 className="mt-6 max-w-xl font-display text-5xl leading-[1.02] text-slate-950 sm:text-6xl">
              Find a care route you can actually follow.
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-8 text-slate-700">
              Compare clinics, cost ranges, transportation, and support programs before you make the trip.
            </p>
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <LandingTile icon={<ShieldAlert />} title="Safety first" text="Flags urgent symptoms before route planning." />
              <LandingTile icon={<BadgeDollarSign />} title="Cost-aware" text="Ranks clinics by affordability and fit." />
              <LandingTile icon={<MapPinned />} title="Route-ready" text="Combines clinics, benefits, and transport into one path." />
            </div>
          </div>

          <section className="rounded-[32px] border border-white/70 bg-white/88 p-6 shadow-[0_32px_90px_rgba(15,23,42,0.12)] backdrop-blur sm:p-8">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">
                  {authMode === "login" ? "Sign in" : "Create account"}
                </p>
                <h2 className="mt-2 font-display text-3xl text-slate-950">
                  {authMode === "login" ? "Continue to your planner" : "Create a private planner"}
                </h2>
              </div>
              <UserRound className="h-6 w-6 text-[#B85C38]" />
            </div>

            <div className="mt-6 inline-flex rounded-full border border-[#E9D9C7] bg-[#FFF7ED] p-1">
              <button
                className={`rounded-full px-4 py-2 text-sm font-semibold ${authMode === "login" ? "bg-[#B85C38] text-white" : "text-slate-700"}`}
                onClick={() => setAuthMode("login")}
              >
                Sign in
              </button>
              <button
                className={`rounded-full px-4 py-2 text-sm font-semibold ${authMode === "register" ? "bg-[#B85C38] text-white" : "text-slate-700"}`}
                onClick={() => setAuthMode("register")}
              >
                Create account
              </button>
            </div>

            <div className="mt-6 grid gap-4">
              {authMode === "register" && (
                <AuthField
                  label="Full name"
                  value={authForm.full_name}
                  onChange={(value) => setAuthForm({ ...authForm, full_name: value })}
                />
              )}
              <AuthField
                label="Email"
                type="email"
                value={authForm.email}
                onChange={(value) => setAuthForm({ ...authForm, email: value })}
              />
              <AuthField
                label="Password"
                type="password"
                value={authForm.password}
                onChange={(value) => setAuthForm({ ...authForm, password: value })}
              />
            </div>

            {error && <ErrorBanner message={error} />}

            <button
              className="focus-ring mt-6 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#B85C38] px-5 py-3 font-semibold text-white hover:bg-[#8F3D2E] disabled:opacity-60"
              onClick={handleAuthSubmit}
              disabled={authLoading}
            >
              {authLoading ? "Please wait..." : authMode === "login" ? "Sign in" : "Create account"}
              <ArrowRight className="h-4 w-4" />
            </button>
          </section>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen pb-12">
      <header className="border-b border-white/60 bg-white/76 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#B85C38]">CareRoute</p>
            <h1 className="mt-1 text-2xl font-semibold text-slate-950">Welcome back, {user.full_name}</h1>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="rounded-full border border-[#E9D9C7] bg-white/80 px-4 py-2 text-sm text-slate-700">
              {user.email}
            </div>
            <button
              className="focus-ring inline-flex items-center gap-2 rounded-full border border-[#D8C9B7] px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-white/70"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-8">
        {error && <ErrorBanner message={error} />}

        <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="space-y-4 xl:sticky xl:top-6 xl:self-start">
            <nav className="rounded-[28px] border border-[#E6DDD1] bg-white p-4 shadow-[0_20px_70px_rgba(15,23,42,0.08)]">
              <button
                className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#B85C38] px-4 py-3 font-semibold text-white hover:bg-[#8F3D2E]"
                onClick={startNewRequest}
              >
                <ArrowRight className="h-4 w-4" />
                New request
              </button>

              <div className="mt-4 space-y-2">
                <SidebarButton label="Profile" active={activeView === "profile"} onClick={() => setActiveView("profile")} />
                <SidebarButton label="History" active={activeView === "history"} onClick={() => setActiveView("history")} />
                <SidebarButton label="Request" active={activeView === "new_request"} onClick={() => setActiveView("new_request")} />
              </div>
            </nav>

            <Panel title="Profile" icon={<UserRound />}>
              <div className="grid gap-3">
                <StatusRow label="Coverage" value={coverageLabel(payload.insurance_status)} />
                <StatusRow label="Provider" value={payload.insurance_provider || "Not provided"} />
                <StatusRow label="Budget" value={`$${payload.budget}`} />
                <StatusRow label="Language" value={payload.language} />
                <StatusRow label="Transport" value={prettyValue(payload.transport_mode)} />
              </div>
            </Panel>

            <Panel title="Recent history" icon={<ClipboardList />}>
              {history.length === 0 ? (
                <p className="text-sm leading-6 text-slate-600">Past care routes will appear here.</p>
              ) : (
                <div className="space-y-3">
                  {history.slice(0, 4).map((item) => (
                    <button
                      key={item.id}
                      className="w-full rounded-[22px] border border-[#EEE2D2] bg-[#FFF9F2] p-4 text-left"
                      onClick={() => setActiveView("history")}
                    >
                      <p className="font-semibold leading-6 text-slate-900">{item.summary}</p>
                      <p className="mt-1 text-sm text-slate-600">{new Date(item.created_at).toLocaleString()}</p>
                    </button>
                  ))}
                </div>
              )}
            </Panel>
          </aside>

          <div className="space-y-6">
            {activeView === "profile" && (
              <ProfileView payload={payload} />
            )}

            {activeView === "history" && (
              <HistoryView history={history} />
            )}

            {activeView === "new_request" && (
              <>
                <StepRail
                  activeStep={activeStep}
                  hasPlan={Boolean(plan)}
                  onSelect={(step) => {
                    if (step === 1 || plan) {
                      setActiveStep(step);
                    }
                  }}
                />

                {activeStep === 1 && (
                  <Stage title="Step 1" heading="Fill out the request" description="Start with the coverage, care need, and access constraints.">
                    <IntakeForm
                      value={payload}
                      loading={planLoading}
                      saving={profileSaving}
                      onChange={setPayload}
                      onSubmit={handleRunRoute}
                      onSave={handleSaveProfile}
                    />
                  </Stage>
                )}

                {activeStep === 2 && plan && activeContent && (
                  <Stage title="Step 2" heading="Review the safety check" description="Make sure the request can proceed before comparing care options.">
                    <div className="space-y-4">
                      <SafetyBanner level={plan.safety.safety_level} message={activeContent.safety_message} />
                      <StageFooter
                        back={() => setActiveStep(1)}
                        next={() => setActiveStep(3)}
                        nextLabel="Continue to payment and support checks"
                      />
                    </div>
                  </Stage>
                )}

                {activeStep === 3 && plan && (
                  <Stage title="Step 3" heading="Check payment fit and support" description="Review self-pay or coverage notes and live public resources before choosing where to go.">
                    <div className="grid gap-4 lg:grid-cols-2">
                      <VerificationCard title="Recommended option" message={plan.insurance_verification.recommended.message} helper={plan.insurance_verification.recommended.member_id_check.message} />
                      <VerificationCard title="Backup option" message={plan.insurance_verification.backup.message} helper={plan.insurance_verification.backup.member_id_check.message} />
                    </div>

                    <Panel title="Live public program lookup" icon={<FileSearch />}>
                      <p className="text-sm leading-6 text-slate-700">{plan.live_eligibility.summary}</p>
                      <div className="mt-4 grid gap-3">
                        {plan.live_eligibility.sources.map((source) => (
                          <EligibilitySourceCard key={source.url} source={source} />
                        ))}
                        {plan.live_eligibility.sources.length === 0 && (
                          <p className="text-sm leading-6 text-slate-600">No live sources were returned for this request.</p>
                        )}
                      </div>
                    </Panel>

                    <StageFooter
                      back={() => setActiveStep(2)}
                      next={() => setActiveStep(4)}
                      nextLabel="Continue to clinic matches"
                    />
                  </Stage>
                )}

                {activeStep === 4 && plan && (
                  <Stage title="Step 4" heading="Compare the clinic options" description="Review the strongest matches before moving to the action plan.">
                    <div className="grid gap-4 lg:grid-cols-2">
                      <CareOptionCard title="Recommended clinic" option={plan.recommended_clinic} highlight />
                      <CareOptionCard title="Backup clinic" option={plan.backup_clinic} />
                    </div>

                    <CareMap plan={plan} />

                    <div className="grid gap-4 md:grid-cols-3">
                      <InfoPanel
                        icon={<MapPinned />}
                        title="Transportation"
                        lines={
                          plan.transportation
                            ? [plan.transportation.name, plan.transportation.estimated_time, plan.transportation.route_summary]
                            : ["No route selected yet"]
                        }
                      />
                      <InfoPanel
                        icon={<Pill />}
                        title="Prescription savings"
                        lines={
                          plan.prescription_savings
                            ? [
                                plan.prescription_savings.name,
                                plan.prescription_savings.generic_support ? "Generic support available" : "Ask about generics",
                                plan.prescription_savings.phone,
                              ]
                            : ["No pharmacy recommendation yet"]
                        }
                      />
                      <Panel title="Support services" icon={<BadgeDollarSign />}>
                        <div className="space-y-3">
                          {plan.city_services.slice(0, 3).map((service) => (
                            <div key={service.id} className="rounded-[22px] border border-[#EEE7DD] bg-[#FCFAF7] p-4">
                              <p className="font-semibold text-slate-900">{service.name}</p>
                              <p className="mt-1 text-sm leading-6 text-slate-600">{service.description}</p>
                            </div>
                          ))}
                        </div>
                      </Panel>
                    </div>

                    <StageFooter
                      back={() => setActiveStep(3)}
                      next={() => setActiveStep(5)}
                      nextLabel="Continue to the action plan"
                    />
                  </Stage>
                )}

                {activeStep === 5 && plan && activeContent && (
                  <Stage title="Step 5" heading="Follow the action plan" description="Use the translated plan, call script, and graph to complete the request.">
                    <section className="rounded-[32px] border border-[#E6DDD1] bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
                      <div className="flex flex-wrap items-start justify-between gap-4">
                        <div className="max-w-3xl">
                          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">Care plan</p>
                          <h2 className="mt-3 text-3xl font-semibold leading-tight text-slate-950">{activeContent.summary}</h2>
                          <p className="mt-3 text-sm leading-7 text-slate-600">{activeContent.disclaimer}</p>
                        </div>
                        <div className="rounded-[24px] border border-[#E9D9C7] bg-[#FFF7ED] p-1">
                          {["English", "Spanish", "Vietnamese"].map((item) => (
                            <button
                              key={item}
                              className={`rounded-[18px] px-4 py-2 text-sm font-semibold ${language === item ? "bg-[#B85C38] text-white" : "text-slate-700"}`}
                              onClick={() => setLanguage(item)}
                            >
                              {item}
                            </button>
                          ))}
                        </div>
                      </div>

                      <div className="mt-6 grid gap-3 lg:grid-cols-2">
                        {activeContent.steps.map((step, index) => (
                          <div key={step} className="rounded-[24px] border border-[#EEE7DD] bg-[#FCFAF7] px-4 py-4">
                            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[#9A4E2D]">Action {index + 1}</p>
                            <p className="mt-2 text-sm leading-6 text-slate-800">{step}</p>
                          </div>
                        ))}
                      </div>

                      <div className="mt-4 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
                        <Panel title="Document checklist" icon={<ClipboardList />}>
                          <ul className="space-y-2 text-sm text-slate-700">
                            {activeContent.documents_needed.map((doc) => (
                              <li key={doc} className="flex gap-2">
                                <span className="mt-2 h-1.5 w-1.5 rounded-full bg-[#B85C38]" />
                                <span>{doc}</span>
                              </li>
                            ))}
                          </ul>
                        </Panel>

                        <Panel title="Call script" icon={<Languages />}>
                          <p className="text-sm leading-7 text-slate-700">{activeContent.call_script}</p>
                        </Panel>
                      </div>
                    </section>
                    <GraphVisualizer graph={plan.graph} />

                    <StageFooter
                      back={() => setActiveStep(4)}
                      next={startNewRequest}
                      nextLabel="Start a new request"
                    />
                  </Stage>
                )}
              </>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}

function LandingTile({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <div className="rounded-[24px] border border-white/70 bg-white/72 p-5 shadow-[0_18px_50px_rgba(15,23,42,0.06)]">
      <div className="text-[#B85C38] [&>svg]:h-5 [&>svg]:w-5">{icon}</div>
      <p className="mt-4 font-semibold text-slate-950">{title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{text}</p>
    </div>
  );
}

function SidebarButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      className={`w-full rounded-[18px] px-4 py-3 text-left text-sm font-semibold ${
        active ? "bg-[#FFF7ED] text-[#8F3D2E]" : "text-slate-700 hover:bg-[#FCFAF7]"
      }`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function StepRail({
  activeStep,
  hasPlan,
  onSelect,
}: {
  activeStep: number;
  hasPlan: boolean;
  onSelect: (step: number) => void;
}) {
  const steps = [
    "Request",
    "Safety",
    "Support",
    "Match",
    "Plan",
  ];

  return (
    <section className="rounded-[28px] border border-[#E6DDD1] bg-white p-4 shadow-[0_20px_70px_rgba(15,23,42,0.08)]">
      <div className="grid gap-3 md:grid-cols-5">
        {steps.map((label, index) => {
          const step = index + 1;
          const disabled = !hasPlan && step > 1;
          return (
            <button
              key={label}
              className={`rounded-[22px] border px-4 py-3 text-left ${
                activeStep === step
                  ? "border-[#D8C0AA] bg-[#FFF7ED]"
                  : "border-[#ECE7DF] bg-[#FCFAF7]"
              } ${disabled ? "opacity-50" : ""}`}
              onClick={() => !disabled && onSelect(step)}
            >
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-500">Step {step}</p>
              <p className="mt-1 text-lg font-semibold text-slate-900">{label}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function Stage({
  title,
  heading,
  description,
  children,
}: {
  title: string;
  heading: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="space-y-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">{title}</p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-950">{heading}</h2>
        <p className="mt-2 text-sm leading-7 text-slate-600">{description}</p>
      </div>
      {children}
    </section>
  );
}

function Panel({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <section className="rounded-[28px] border border-[#E6DDD1] bg-white p-5 shadow-[0_20px_70px_rgba(15,23,42,0.08)]">
      <div className="mb-4 flex items-center gap-2 text-slate-900">
        <span className="text-[#B85C38] [&>svg]:h-5 [&>svg]:w-5">{icon}</span>
        <h3 className="text-xl font-semibold text-slate-950">{title}</h3>
      </div>
      {children}
    </section>
  );
}

function InfoPanel({ icon, title, lines }: { icon: ReactNode; title: string; lines: string[] }) {
  return (
    <Panel title={title} icon={icon}>
      <div className="space-y-2 text-sm text-slate-700">
        {lines.map((line) => (
          <p key={line}>{line}</p>
        ))}
      </div>
    </Panel>
  );
}

function VerificationCard({ title, message, helper }: { title: string; message: string; helper: string }) {
  return (
    <div className="rounded-[28px] border border-[#E6DDD1] bg-white p-5 shadow-[0_20px_70px_rgba(15,23,42,0.08)]">
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">{title}</p>
      <p className="mt-3 text-base font-semibold leading-7 text-slate-950">{message}</p>
      <p className="mt-3 text-sm leading-6 text-slate-600">{helper}</p>
    </div>
  );
}

function EligibilitySourceCard({ source }: { source: LiveEligibilitySource }) {
  return (
    <a
      className="block rounded-[22px] border border-[#EEE7DD] bg-[#FCFAF7] p-4 hover:border-[#D8C0AA]"
      href={source.url}
      target="_blank"
      rel="noreferrer"
    >
      <p className="font-semibold text-slate-900">{source.title}</p>
      <p className="mt-2 text-sm leading-6 text-slate-600">{source.snippet}</p>
      <p className="mt-3 text-sm font-medium text-[#8F3D2E]">{source.url}</p>
    </a>
  );
}

function StageFooter({
  back,
  next,
  nextLabel,
}: {
  back: () => void;
  next: () => void;
  nextLabel: string;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <button
        className="focus-ring rounded-full border border-[#D8C9B7] px-4 py-2 text-sm font-semibold text-slate-900 hover:bg-[#FFF7ED]"
        onClick={back}
      >
        Back
      </button>
      <button
        className="focus-ring inline-flex items-center gap-2 rounded-full bg-[#B85C38] px-4 py-2 text-sm font-semibold text-white hover:bg-[#8F3D2E]"
        onClick={next}
      >
        {nextLabel}
        <ArrowRight className="h-4 w-4" />
      </button>
    </div>
  );
}

function ProfileView({ payload }: { payload: IntakePayload }) {
  return (
    <section className="space-y-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">Profile</p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-950">Saved request profile</h2>
        <p className="mt-2 text-sm leading-7 text-slate-600">This is the current information that will be used the next time you start a care request.</p>
      </div>

      <Panel title="Coverage details" icon={<UserRound />}>
        <div className="grid gap-3 md:grid-cols-2">
          <StatusRow label="Coverage type" value={coverageLabel(payload.insurance_status)} />
          <StatusRow label="Provider" value={payload.insurance_provider || "Not provided"} />
          <StatusRow label="Plan name" value={payload.insurance_plan || "Not provided"} />
          <StatusRow label="Member ID" value={payload.member_id || "Not provided"} />
          <StatusRow label="ZIP code" value={payload.zip_code || "Not provided"} />
          <StatusRow label="Care need" value={payload.care_need || "Not provided"} />
        </div>
      </Panel>
    </section>
  );
}

function HistoryView({ history }: { history: HistoryItem[] }) {
  return (
    <section className="space-y-4">
      <div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#B85C38]">History</p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-950">Past care requests</h2>
        <p className="mt-2 text-sm leading-7 text-slate-600">Review past summaries and the clinic recommendations that were returned.</p>
      </div>

      <div className="grid gap-4">
        {history.length === 0 ? (
          <Panel title="No history yet" icon={<ClipboardList />}>
            <p className="text-sm leading-6 text-slate-600">Run a request first and it will appear here.</p>
          </Panel>
        ) : (
          history.map((item) => (
            <Panel key={item.id} title={item.recommended_clinic ?? "Care route"} icon={<ClipboardList />}>
              <p className="text-base font-semibold leading-7 text-slate-950">{item.summary}</p>
              <p className="mt-2 text-sm leading-6 text-slate-600">{new Date(item.created_at).toLocaleString()}</p>
              {item.backup_clinic && <p className="mt-2 text-sm text-slate-700">Backup clinic: {item.backup_clinic}</p>}
            </Panel>
          ))
        )}
      </div>
    </section>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-[22px] border border-[#EEE7DD] bg-[#FCFAF7] px-4 py-3 text-sm">
      <span className="text-slate-600">{label}</span>
      <span className="font-medium text-slate-900">{value || "Not set"}</span>
    </div>
  );
}

function AuthField({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="text-sm font-medium text-slate-700">
      {label}
      <input
        className="focus-ring mt-1 w-full rounded-2xl border border-[#D8C9B7] bg-white px-4 py-3"
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-[#F2B6A0] bg-[#FFF1EB] px-4 py-3 text-sm text-[#8F3D2E]">
      {message}
    </div>
  );
}

function coverageLabel(value: string) {
  return COVERAGE_OPTIONS.find((item) => item.value === value)?.label ?? prettyValue(value);
}

function prettyValue(value: string) {
  return value.replace(/_/g, " ");
}
