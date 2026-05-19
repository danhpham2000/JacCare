# CareRoute AI Architecture

## Runtime Shape

The backend has two entry surfaces over the same care engine:

- `backend/main.jac`: Jac graph model and public walkers.
- `backend/app.py`: FastAPI adapter exposing the `/api/*` endpoints used by the web app.

The ranking, safety, eligibility, pharmacy, and graph payload logic lives in `backend/services/care_engine.py` so both surfaces remain consistent.

## Graph Model

Jac node types:

- `UserProfile`
- `Clinic`
- `Pharmacy`
- `CityService`
- `TransportRoute`
- `EligibilityRule`
- `CostOption`

Jac edge types:

- `Nearby`
- `EligibleFor`
- `ReachableBy`
- `BudgetMatch`
- `Offers`

## Walker Flow

`FullCareRouteWalker` seeds the graph, creates the user profile, runs safety logic, ranks care options, generates a plan, and returns graph data.

Specialized walkers are also exposed:

- `SeedGraphWalker`: loads seeded resources into the Jac graph.
- `IntakeWalker`: normalizes and persists a user profile.
- `SafetyWalker`: applies deterministic emergency checks.
- `CareMatchWalker`: visits clinic nodes and returns ranked matches.
- `EligibilityWalker`: visits service nodes and returns likely support programs.
- `TransportWalker`: visits route nodes and returns graph route data.
- `CostRankWalker`: returns score breakdowns.
- `PlanExplainWalker`: calls `by llm()` when configured, with deterministic fallback.
- `CallScriptWalker`: generates call scripts and translation fallback.

## API Adapter

The frontend calls:

- `POST /api/intake`
- `POST /api/safety-check`
- `POST /api/match-care`
- `POST /api/generate-plan`
- `POST /api/generate-call-script`
- `POST /api/translate`
- `GET /api/graph`
- `POST /api/graph`
- `POST /api/run-care-route`

## Safety Boundary

The LLM is never the sole decision-maker for medical urgency, diagnosis, eligibility, or price guarantees. Emergency routing is deterministic and runs before plan text. Generated content is limited to explanation, call scripts, translation, and simplification.
