# JacCareRoute

JacCareRoute is a Jac-backed healthcare and city-service navigator for uninsured or low-income users. It matches a user’s ZIP code, budget, transportation access, language, care need, urgency, and household context against a graph of clinics, pharmacies, transit routes, cost options, and public assistance programs.

JacCareRoute is not an AI doctor. It is a care-access planner that helps answer: where to go, what it may cost, how to get there, what to bring, what support programs may help, and what to say when calling.

## What Is Built

- Jac nodes for `UserProfile`, `Clinic`, `Pharmacy`, `CityService`, `TransportRoute`, `EligibilityRule`, and `CostOption`
- Jac walkers for intake, safety, care matching, eligibility, transport, cost ranking, plan explanation, and call scripts
- Rule-based emergency red-flag screening before generated text
- Deterministic ranking with the requested weights
- FastAPI adapter exposing the spec’s `/api/*` routes
- Authenticated React + TypeScript + Tailwind frontend with a step-by-step intake and care-planning flow
- Leaflet map, graph visualization, translated care plans, call scripts, and recent request history
- Seeded Austin city dataset with 10 clinics, 5 pharmacies, 5 services, 5 routes, 10 eligibility rules, and 10 cost options
- Live public-program lookup to supplement the seeded graph with current support resources

## Core Story

The core workflow is:

1. Collect practical constraints: ZIP code, budget, language, transport, care need, urgency, and household context.
2. Run deterministic safety checks for red-flag symptoms.
3. Rank affordable care options, with strong preference for uninsured access, sliding-scale support, reachable transport, and language fit.
4. Surface public programs, prescription savings, document needs, and a call script the user can actually use.

Coverage details can be provided when the user has them, but the app does not attempt to act like a claims processor or a network-verification system. Coverage is treated as one input into a broader care-access plan.

## Run Backend API

```bash
python3 -m venv .venv
./.venv/bin/pip install -r backend/requirements.txt
cd backend
../.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8010
```

Health check:

```bash
curl -sS http://127.0.0.1:8010/health
```

End-to-end API smoke test:

```bash
curl -sS -X POST http://127.0.0.1:8010/api/run-care-route \
  -H 'Content-Type: application/json' \
  -d '{"zip_code":"78705","insurance_status":"uninsured","budget":50,"language":"Spanish","transport_mode":"public_transit","care_need":"child fever","urgency":"today","household":"single parent with one child"}'
```

## Run Jac Walkers

Install Jac if needed:

```bash
pip install jaseci
```

Run the Jac backend directly:

```bash
cd backend
jac run main.jac
```

Serve public Jac walkers:

```bash
cd backend
jac start main.jac
```

The main end-to-end walker is `FullCareRouteWalker`.

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173).

The backend also serves the built frontend at [http://127.0.0.1:8010](http://127.0.0.1:8010) after `npm run build`.

## Production Build

```bash
cd frontend
npm run build
```

## Safety

JacCareRoute avoids diagnosis and treatment advice. It uses deterministic checks for red-flag terms such as trouble breathing, chest pain, severe allergic reaction, loss of consciousness, severe bleeding, stroke symptoms, severe dehydration, infant fever concerns, and self-harm risk. Any eligibility, cost, or availability result is framed as an estimate that should be confirmed directly with the clinic or program office.
