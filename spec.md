# CareRoute AI MVP Spec Summary

CareRoute AI matches uninsured or low-income users to affordable clinics, prescription savings, transportation routes, and public assistance programs using Jac graph walkers.

The MVP supports one seeded Austin demo dataset. Users provide ZIP code, insurance status, budget, transportation access, language, care need, urgency, and household situation. The system returns a recommended clinic, backup clinic, estimated cost, transportation option, documents, city services, prescription savings, call script, translation, and graph visualization.

Non-goals: diagnosis, treatment advice, real claims, real medical records, guaranteed prices, guaranteed benefit eligibility, or emergency decision replacement.

Core walkers:

- `IntakeWalker`
- `SafetyWalker`
- `CareMatchWalker`
- `EligibilityWalker`
- `TransportWalker`
- `CostRankWalker`
- `PlanExplainWalker`
- `CallScriptWalker`
- `FullCareRouteWalker`

Ranking weights:

- Cost fit: 30
- Insurance or sliding-scale match: 20
- Distance: 15
- Transportation access: 10
- Language match: 10
- Care need match: 10
- Document simplicity: 5
