from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import json
import math
import re
import uuid


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"

RED_FLAGS = {
    "trouble breathing": "Emergency care recommended: trouble breathing can be life-threatening.",
    "can't breathe": "Emergency care recommended: breathing difficulty can be life-threatening.",
    "chest pain": "Emergency care recommended: chest pain can be life-threatening.",
    "severe allergic": "Emergency care recommended: severe allergic reactions need immediate care.",
    "anaphylaxis": "Emergency care recommended: severe allergic reactions need immediate care.",
    "loss of consciousness": "Emergency care recommended: loss of consciousness needs immediate care.",
    "unconscious": "Emergency care recommended: loss of consciousness needs immediate care.",
    "severe bleeding": "Emergency care recommended: severe bleeding needs immediate care.",
    "stroke": "Emergency care recommended: stroke symptoms need immediate care.",
    "face drooping": "Emergency care recommended: possible stroke symptoms need immediate care.",
    "severe dehydration": "Emergency care recommended: severe dehydration needs immediate care.",
    "suicidal": "Emergency care recommended: immediate self-harm risk needs urgent support.",
    "self-harm": "Emergency care recommended: immediate self-harm risk needs urgent support.",
}

CARE_KEYWORDS = {
    "pediatric care": ["child", "kid", "baby", "infant", "fever", "school"],
    "urgent care": ["today", "urgent", "same-day", "infection", "injury"],
    "primary care": ["checkup", "general", "cough", "cold", "fever", "primary"],
    "mental health": ["anxiety", "depression", "counseling", "mental"],
    "dental care": ["tooth", "dental", "gum", "mouth"],
    "prenatal care": ["pregnant", "prenatal", "pregnancy"],
    "prescription support": ["prescription", "medication", "refill", "medicine"],
}

ZIP_COORDS = {
    "78701": (30.2711, -97.7437),
    "78702": (30.2604, -97.7136),
    "78703": (30.2890, -97.7664),
    "78704": (30.2457, -97.7688),
    "78705": (30.2924, -97.7386),
    "78721": (30.2747, -97.6860),
    "78722": (30.2894, -97.7166),
    "78723": (30.3075, -97.6847),
    "78741": (30.2316, -97.7144),
    "78745": (30.2065, -97.7954),
    "78752": (30.3314, -97.7047),
}

TRANSLATED_TERMS = {
    "spanish": {
        "today": "hoy",
        "now": "ahora",
        "this week": "esta semana",
        "routine": "de rutina",
        "child fever": "fiebre infantil",
        "primary care": "atencion primaria",
        "prescription support": "apoyo con recetas",
    },
    "vietnamese": {
        "today": "hom nay",
        "now": "ngay bay gio",
        "this week": "tuan nay",
        "routine": "kham dinh ky",
        "child fever": "sot o tre",
        "primary care": "cham soc ban dau",
        "prescription support": "ho tro toa thuoc",
    },
}

DOCUMENT_TRANSLATIONS = {
    "spanish": {
        "Photo ID if available": "Identificacion con foto si la tiene",
        "Proof of income if available": "Comprobante de ingresos si lo tiene",
        "Any current medications": "Medicamentos actuales",
        "Child's basic information": "Informacion basica del menor",
        "Proof of residence if available": "Comprobante de domicilio si lo tiene",
        "Child identification": "Identificacion del menor",
        "Appointment details": "Detalles de la cita",
        "Proof of income": "Comprobante de ingresos",
        "Income information if available": "Informacion de ingresos si la tiene",
        "Household size": "Tamano del hogar",
        "Prescription name": "Nombre de la receta",
        "Phone number for callback": "Numero de telefono para devolucion de llamada",
        "Vaccine record if available": "Registro de vacunas si lo tiene",
        "Medication list": "Lista de medicamentos",
        "Student ID if available": "Identificacion estudiantil si la tiene",
        "None required for first visit": "No se requiere nada para la primera visita",
        "Proof of pregnancy if available": "Comprobante de embarazo si lo tiene",
        "No immigration documents required for navigation services": "No se requieren documentos migratorios para servicios de orientacion",
    },
    "vietnamese": {
        "Photo ID if available": "Giay to tuy than co anh neu co",
        "Proof of income if available": "Giay to chung minh thu nhap neu co",
        "Any current medications": "Danh sach thuoc dang dung",
        "Child's basic information": "Thong tin co ban cua tre",
        "Proof of residence if available": "Giay to cu tru neu co",
        "Child identification": "Giay to cua tre",
        "Appointment details": "Thong tin lich hen",
        "Proof of income": "Giay to chung minh thu nhap",
        "Income information if available": "Thong tin thu nhap neu co",
        "Household size": "So nguoi trong ho",
        "Prescription name": "Ten don thuoc",
        "Phone number for callback": "So dien thoai de goi lai",
        "Vaccine record if available": "So tiem chung neu co",
        "Medication list": "Danh sach thuoc",
        "Student ID if available": "The sinh vien neu co",
        "None required for first visit": "Khong can giay to cho lan kham dau",
        "Proof of pregnancy if available": "Giay to xac nhan mang thai neu co",
        "No immigration documents required for navigation services": "Khong can giay to di tru cho dich vu huong dan",
    },
}

TRANSLATIONS = {
    "spanish": {
        "Your strongest care-access option is": "Su mejor opcion de acceso a atencion es",
        "with an estimated visit cost of": "con un costo estimado de visita de",
        "Call the clinic before going and confirm same-day availability.": "Llame a la clinica antes de ir y confirme disponibilidad el mismo dia.",
        "Ask about sliding-scale pricing and the estimated visit cost.": "Pregunte por el pago segun ingresos y el costo estimado de la visita.",
        "Bring the listed documents if available; do not delay care if you are missing optional documents.": "Lleve los documentos indicados si los tiene; no retrase la atencion si le faltan documentos opcionales.",
        "No emergency red flags detected from the provided information. This does not replace medical advice.": "No se detectaron senales de emergencia con la informacion proporcionada. Esto no reemplaza el consejo medico.",
        "No emergency red flags were detected, but same-day professional care may be appropriate. This does not replace medical advice.": "No se detectaron senales de emergencia, pero puede ser apropiada atencion profesional el mismo dia. Esto no reemplaza el consejo medico.",
    },
    "vietnamese": {
        "Your strongest care-access option is": "Lua chon tiep can cham soc phu hop nhat cua ban la",
        "with an estimated visit cost of": "voi chi phi uoc tinh cho lan kham la",
        "Call the clinic before going and confirm same-day availability.": "Hay goi cho phong kham truoc khi den va xac nhan lich kham trong ngay.",
        "Ask about sliding-scale pricing and the estimated visit cost.": "Hay hoi ve muc phi theo thu nhap va chi phi uoc tinh cho lan kham.",
        "Bring the listed documents if available; do not delay care if you are missing optional documents.": "Hay mang theo cac giay to duoc liet ke neu co; dung tri hoan viec di kham neu ban thieu giay to khong bat buoc.",
        "No emergency red flags detected from the provided information. This does not replace medical advice.": "Khong phat hien dau hieu cap cuu tu thong tin da cung cap. Dieu nay khong thay the tu van y khoa.",
        "No emergency red flags were detected, but same-day professional care may be appropriate. This does not replace medical advice.": "Khong phat hien dau hieu cap cuu, nhung viec duoc kham trong ngay co the phu hop. Dieu nay khong thay the tu van y khoa.",
    },
}


def load_json(name: str) -> list[dict[str, Any]]:
    with (DATA_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_dataset() -> dict[str, list[dict[str, Any]]]:
    return {
        "clinics": load_json("clinics.json"),
        "pharmacies": load_json("pharmacies.json"),
        "city_services": load_json("city_services.json"),
        "transport_routes": load_json("transport_routes.json"),
        "eligibility_rules": load_json("eligibility_rules.json"),
        "cost_options": load_json("cost_options.json"),
    }


def normalize_intake(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_id": payload.get("user_id") or f"user_{uuid.uuid4().hex[:8]}",
        "zip_code": str(payload.get("zip_code", "")).strip() or "78705",
        "insurance_status": str(payload.get("insurance_status", "uninsured")).strip().lower(),
        "insurance_provider": str(payload.get("insurance_provider", "")).strip(),
        "insurance_plan": str(payload.get("insurance_plan", "")).strip(),
        "member_id": str(payload.get("member_id", "")).strip(),
        "budget": int(payload.get("budget") or 50),
        "language": str(payload.get("language", "English")).strip() or "English",
        "transport_mode": str(payload.get("transport_mode", "public_transit")).strip().lower(),
        "care_need": str(payload.get("care_need", "primary care")).strip().lower(),
        "urgency": str(payload.get("urgency", "today")).strip().lower(),
        "household": str(payload.get("household", payload.get("household_type", ""))).strip(),
    }


def language_key(language: str) -> str:
    target = (language or "English").strip().lower()
    if target.startswith("spanish"):
        return "spanish"
    if target.startswith("vietnamese"):
        return "vietnamese"
    return "english"


def language_label(language: str) -> str:
    key = language_key(language)
    if key == "spanish":
        return "Spanish"
    if key == "vietnamese":
        return "Vietnamese"
    return "English"


def translate_term(text: str, language: str) -> str:
    key = language_key(language)
    return TRANSLATED_TERMS.get(key, {}).get(text.lower(), text)


def translate_document(doc: str, language: str) -> str:
    key = language_key(language)
    return DOCUMENT_TRANSLATIONS.get(key, {}).get(doc, doc)


def care_category(care_need: str, urgency: str = "") -> str:
    text = f"{care_need} {urgency}".lower()
    for category, terms in CARE_KEYWORDS.items():
        if any(term in text for term in terms):
            return category
    return "primary care"


def safety_check(payload: dict[str, Any]) -> dict[str, Any]:
    profile = normalize_intake(payload)
    text = f"{profile['care_need']} {profile['urgency']}".lower()
    for phrase, message in RED_FLAGS.items():
        if phrase in text:
            return {
                "safety_level": "emergency",
                "red_flags": [phrase],
                "message": message
                + " Call 911 or go to the nearest emergency department. CareRoute AI is not a medical provider.",
                "continue_matching": True,
            }
    if any(term in text for term in ["infant fever", "baby fever", "high fever", "same-day", "today"]):
        return {
            "safety_level": "urgent_care_recommended",
            "red_flags": [],
            "message": "No emergency red flags were detected, but same-day professional care may be appropriate. This does not replace medical advice.",
            "continue_matching": True,
        }
    return {
        "safety_level": "non_emergency",
        "red_flags": [],
        "message": "No emergency red flags detected from the provided information. This does not replace medical advice.",
        "continue_matching": True,
    }


def distance_miles(zip_a: str, zip_b: str) -> float:
    a = ZIP_COORDS.get(zip_a, ZIP_COORDS["78705"])
    b = ZIP_COORDS.get(zip_b, ZIP_COORDS["78705"])
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return round(3958.8 * 2 * math.asin(math.sqrt(h)), 1)


def stable_coordinate(zip_code: str, identifier: str) -> tuple[float, float]:
    base_lat, base_lon = ZIP_COORDS.get(zip_code, ZIP_COORDS["78705"])
    spread = sum(ord(char) for char in identifier)
    lat_offset = ((spread % 11) - 5) * 0.0032
    lon_offset = (((spread // 11) % 11) - 5) * 0.0034
    return round(base_lat + lat_offset, 6), round(base_lon + lon_offset, 6)


def annotate_location(item: dict[str, Any], zip_code: Optional[str], identifier: Optional[str] = None) -> dict[str, Any]:
    if not zip_code:
        return item
    latitude, longitude = stable_coordinate(zip_code, identifier or item.get("id", zip_code))
    return {**item, "latitude": latitude, "longitude": longitude}


def user_coordinates(profile: dict[str, Any]) -> dict[str, float]:
    latitude, longitude = stable_coordinate(profile["zip_code"], profile["user_id"])
    return {"latitude": latitude, "longitude": longitude}


def route_for(clinic_id: str, transport_mode: str, routes: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    normalized = transport_mode.replace("-", "_")
    matches = [
        route
        for route in routes
        if clinic_id in route.get("clinic_ids", [])
        and (route.get("mode") == normalized or route.get("type") == normalized)
    ]
    if matches:
        return sorted(matches, key=lambda r: (r.get("estimated_cost", 99), r.get("estimated_minutes", 999)))[0]
    if normalized in {"public_transit", "phone"}:
        return None
    fallback = [route for route in routes if clinic_id in route.get("clinic_ids", [])]
    return fallback[0] if fallback else None


def insurance_verification_message(profile: dict[str, Any], clinic: Optional[dict[str, Any]]) -> dict[str, Any]:
    if clinic is None:
        return {
            "status": "unknown",
            "message": "No clinic was selected, so coverage could not be checked.",
            "member_id_check": member_id_check(profile.get("member_id", "")),
        }

    status = profile["insurance_status"]
    provider = profile.get("insurance_provider", "").strip()
    provider_label = provider or status.replace("_", " ")
    member_check = member_id_check(profile.get("member_id", ""))

    if status == "uninsured":
        if clinic.get("accepts_uninsured"):
            return {
                "status": "self_pay_supported",
                "message": f"{clinic['name']} appears workable for self-pay care. Sliding-scale or cash-pay options should be asked about directly.",
                "member_id_check": member_check,
            }
        return {
            "status": "call_first",
            "message": f"{clinic['name']} may not be a strong uninsured option. Call first before visiting.",
            "member_id_check": member_check,
        }

    if status in {"medicaid", "chip"}:
        accepted = clinic.get("accepts_medicaid", False)
        return {
            "status": "likely_accepted" if accepted else "call_first",
            "message": (
                f"{clinic['name']} likely accepts {provider_label}. Bring the card and member number if you have them."
                if accepted
                else f"{clinic['name']} may not accept {provider_label}. Call first and ask whether they can still see you under self-pay or sliding scale."
            ),
            "member_id_check": member_check,
        }

    if status in {"medicare", "aca_marketplace", "employer_plan", "underinsured", "tricare", "va"}:
        return {
            "status": "network_check_needed",
            "message": f"CareRoute cannot confirm network status for {provider_label}. Call {clinic['name']} and verify participation before the visit.",
            "member_id_check": member_check,
        }

    return {
        "status": "call_first",
        "message": f"Coverage details for {provider_label} should be verified directly with {clinic['name']}.",
        "member_id_check": member_check,
    }


def member_id_check(member_id: str) -> dict[str, Any]:
    cleaned = member_id.replace(" ", "").replace("-", "")
    if not cleaned:
        return {"status": "missing", "message": "No member ID was provided."}
    if 5 <= len(cleaned) <= 20 and cleaned.isalnum():
        return {"status": "format_ok", "message": "The member ID format looks usable for a phone verification call."}
    return {"status": "check_format", "message": "The member ID format looks unusual. Recheck the card before calling."}


def clinic_scores(profile: dict[str, Any], dataset: Optional[dict[str, list[dict[str, Any]]]] = None) -> list[dict[str, Any]]:
    data = dataset or load_dataset()
    desired_category = care_category(profile["care_need"], profile["urgency"])
    results: list[dict[str, Any]] = []

    for clinic in data["clinics"]:
        services = [service.lower() for service in clinic.get("services", [])]
        distance = clinic.get("distance_miles") or distance_miles(profile["zip_code"], clinic["zip_code"])
        route = route_for(clinic["id"], profile["transport_mode"], data["transport_routes"])

        cost_score = 100 if clinic["estimated_min_cost"] <= profile["budget"] else max(0, 100 - (clinic["estimated_min_cost"] - profile["budget"]) * 3)
        if clinic["estimated_max_cost"] <= profile["budget"]:
            cost_score = 100
        elif clinic["estimated_min_cost"] <= profile["budget"]:
            cost_score = max(cost_score, 82)

        insurance_match = 100 if (
            (profile["insurance_status"] == "uninsured" and clinic["accepts_uninsured"])
            or (profile["insurance_status"] in {"medicaid", "chip"} and clinic["accepts_medicaid"])
            or profile["insurance_status"] not in {"uninsured", "medicaid", "chip"}
        ) else 25
        if clinic["sliding_scale"]:
            insurance_match = min(100, insurance_match + 15)

        distance_score = max(0, 100 - distance * 12)
        transport_score = 100 if route else (70 if profile["transport_mode"] == "car" else 30)
        language_score = 100 if profile["language"].lower() in [lang.lower() for lang in clinic["languages"]] else 55
        if desired_category in services:
            care_score = 100
        elif desired_category == "pediatric care" and "primary care" in services:
            care_score = 70
        elif desired_category == "urgent care" and "primary care" in services:
            care_score = 65
        else:
            care_score = 55
        doc_count = len(clinic.get("documents_required", []))
        document_score = max(45, 100 - doc_count * 10)

        score = round(
            cost_score * 0.30
            + insurance_match * 0.20
            + distance_score * 0.15
            + transport_score * 0.10
            + language_score * 0.10
            + care_score * 0.10
            + document_score * 0.05
        )

        reason_parts = []
        if profile["insurance_status"] == "uninsured" and clinic["accepts_uninsured"]:
            reason_parts.append("accepts uninsured patients")
        elif profile["insurance_status"] in {"medicaid", "chip"} and clinic["accepts_medicaid"]:
            reason_parts.append(f"likely works with {profile.get('insurance_provider') or profile['insurance_status']}")
        if clinic["sliding_scale"]:
            reason_parts.append("offers sliding-scale pricing")
        if profile["language"] in clinic["languages"]:
            reason_parts.append(f"supports {profile['language']}")
        if route:
            reason_parts.append(f"is reachable by {route['name']}")
        if desired_category in services:
            reason_parts.append(f"matches {desired_category}")

        base_result = {
            **clinic,
            "score": int(score),
            "distance": f"{distance:.1f} miles",
            "distance_miles": distance,
            "estimated_cost": f"${clinic['estimated_min_cost']}-${clinic['estimated_max_cost']}",
            "transportation": route,
            "reason": "This option " + ", ".join(reason_parts) + ".",
            "insurance_verification": insurance_verification_message(profile, clinic),
            "score_breakdown": {
                "cost_fit": round(cost_score),
                "insurance_or_sliding_scale": round(insurance_match),
                "distance": round(distance_score),
                "transportation": round(transport_score),
                "language": round(language_score),
                "care_need": round(care_score),
                "documents": round(document_score),
            },
        }
        results.append(annotate_location(base_result, clinic["zip_code"], clinic["id"]))

    return sorted(results, key=lambda item: item["score"], reverse=True)


def eligible_services(profile: dict[str, Any], dataset: Optional[dict[str, list[dict[str, Any]]]] = None) -> list[dict[str, Any]]:
    data = dataset or load_dataset()
    household = profile.get("household", "").lower()
    services = []
    for service in data["city_services"]:
        category = service.get("category", "").lower()
        score = 0
        if profile["insurance_status"] == "uninsured" and category in {"health insurance", "clinic navigation", "prescription assistance"}:
            score += 35
        if "child" in household or "parent" in household or "family" in household:
            if "chip" in service["name"].lower() or category in {"food support", "health insurance"}:
                score += 35
        if profile["transport_mode"] in {"public_transit", "no_car"} and category == "transportation":
            score += 35
        if profile["language"].lower() in [language.lower() for language in service.get("languages", [])]:
            score += 15
        if score > 0:
            services.append(
                {
                    **service,
                    "match_score": min(100, score),
                    "eligibility_note": "You may qualify based on the limited demo information. Confirm with the program office.",
                }
            )
    return sorted(services, key=lambda item: item["match_score"], reverse=True)[:5]


def pharmacy_options(profile: dict[str, Any], dataset: Optional[dict[str, list[dict[str, Any]]]] = None) -> list[dict[str, Any]]:
    data = dataset or load_dataset()
    pharmacies = []
    for pharmacy in data["pharmacies"]:
        distance = pharmacy.get("distance_miles") or distance_miles(profile["zip_code"], pharmacy["zip_code"])
        lang = profile["language"].lower() in [language.lower() for language in pharmacy.get("languages", [])]
        score = 60 + (25 if pharmacy.get("discount_available") else 0) + (10 if pharmacy.get("generic_support") else 0) + (5 if lang else 0) - min(20, distance * 3)
        enriched = annotate_location({**pharmacy, "score": round(score), "distance": f"{distance:.1f} miles"}, pharmacy["zip_code"], pharmacy["id"])
        pharmacies.append(enriched)
    return sorted(pharmacies, key=lambda item: item["score"], reverse=True)[:3]


def documents_needed(top: Optional[dict[str, Any]], services: list[dict[str, Any]]) -> list[str]:
    docs = ["Photo ID if available", "Proof of income if available", "Any current medications"]
    if top:
        docs.extend(top.get("documents_required", []))
    for service in services[:2]:
        docs.extend(service.get("documents_required", []))
    seen = set()
    result = []
    for doc in docs:
        key = doc.lower()
        if key not in seen:
            seen.add(key)
            result.append(doc)
    return result[:8]


def build_call_script(profile: dict[str, Any], clinic: Optional[dict[str, Any]] = None, language: Optional[str] = None) -> str:
    target_language = language_key(language or profile.get("language", "English"))
    clinic_name = clinic["name"] if clinic else "the clinic"
    care_need = translate_term(profile["care_need"], target_language)
    urgency = translate_term(profile["urgency"], target_language)

    if target_language == "spanish":
        return (
            f"Hola, no tengo seguro y busco atencion {urgency} en {clinic_name} por {care_need}. "
            "Aceptan pago segun ingresos? Que documentos debo llevar? "
            "Cual es el costo estimado de una visita? Hay disponibilidad el mismo dia y apoyo con recetas o beneficios?"
        )
    if target_language == "vietnamese":
        return (
            f"Xin chao, toi khong co bao hiem va dang tim lich kham {urgency} tai {clinic_name} cho van de {care_need}. "
            "Phong kham co tinh phi theo thu nhap khong? Toi nen mang theo giay to nao? "
            "Chi phi uoc tinh cho mot lan kham la bao nhieu? Hom nay con lich va co ho tro ve toa thuoc hoac chuong trinh ho tro khong?"
        )
    return (
        f"Hi, I am {profile['insurance_status']} and looking for {profile['urgency']} care at {clinic_name} "
        f"for {profile['care_need']}. Do you accept sliding-scale payment? "
        "What documents should I bring? What is the estimated cost for a visit? "
        "Is there same-day availability, and can you help with prescription or benefits referrals?"
    )


def localized_summary(top: Optional[dict[str, Any]], safety: dict[str, Any], language: str) -> str:
    key = language_key(language)
    if safety["safety_level"] == "emergency":
        if key == "spanish":
            return "Se detectaron senales de emergencia. Llame al 911 o vaya a atencion de emergencia ahora."
        if key == "vietnamese":
            return "Da phat hien dau hieu cap cuu. Hay goi 911 hoac den khoa cap cuu ngay bay gio."
        return "Emergency red flags were detected. Call 911 or seek emergency care now."

    if not top:
        if key == "spanish":
            return "No se encontro una clinica adecuada con el conjunto de datos actual."
        if key == "vietnamese":
            return "Khong tim thay phong kham phu hop trong bo du lieu hien tai."
        return "No matching clinic was found in the current city dataset."

    if key == "spanish":
        return f"La opcion de atencion mas viable es {top['name']} con un costo estimado de {top['estimated_cost']}."
    if key == "vietnamese":
        return f"Lua chon cham soc kha thi nhat la {top['name']} voi chi phi uoc tinh {top['estimated_cost']}."
    return f"Your strongest care-access option is {top['name']} with an estimated visit cost of {top['estimated_cost']}."


def localized_steps(route: Optional[dict[str, Any]], pharmacy: Optional[dict[str, Any]], language: str) -> list[str]:
    key = language_key(language)
    if key == "spanish":
        steps = [
            "Llame a la clinica antes de ir y confirme disponibilidad el mismo dia.",
            "Pregunte por el pago segun ingresos y el costo estimado de la visita.",
            "Lleve los documentos indicados si los tiene; no retrase la atencion si le faltan documentos opcionales.",
        ]
        if route:
            steps.append(f"Use {route['name']}: {route['route_summary']}.")
        if pharmacy:
            steps.append(f"Pregunte por opciones genericas o de descuento en {pharmacy['name']}.")
        return steps

    if key == "vietnamese":
        steps = [
            "Hay goi cho phong kham truoc khi den va xac nhan lich kham trong ngay.",
            "Hay hoi ve muc phi theo thu nhap va chi phi uoc tinh cho lan kham.",
            "Hay mang theo cac giay to duoc liet ke neu co; dung tri hoan viec di kham neu ban thieu giay to khong bat buoc.",
        ]
        if route:
            steps.append(f"Su dung {route['name']}: {route['route_summary']}.")
        if pharmacy:
            steps.append(f"Hay hoi ve thuoc generic hoac chuong trinh giam gia tai {pharmacy['name']}.")
        return steps

    steps = [
        "Call the clinic before going and confirm same-day availability.",
        "Ask about sliding-scale pricing and the estimated visit cost.",
        "Bring the listed documents if available; do not delay care if you are missing optional documents.",
    ]
    if route:
        steps.append(f"Use {route['name']}: {route['route_summary']}.")
    if pharmacy:
        steps.append(f"Ask about generic or discount options at {pharmacy['name']}.")
    return steps


def localized_disclaimer(language: str) -> str:
    key = language_key(language)
    if key == "spanish":
        return "CareRoute AI es una herramienta de navegacion, no un proveedor medico. Los costos y la elegibilidad son estimaciones; llame directamente para confirmar."
    if key == "vietnamese":
        return "CareRoute AI la cong cu huong dan, khong phai nha cung cap y te. Chi phi va dieu kien duoc tinh chi la uoc tinh; hay lien he truc tiep de xac nhan."
    return "CareRoute AI is a navigation tool, not a medical provider. Costs and eligibility are estimates; call programs directly to confirm."


def localized_safety(safety: dict[str, Any], language: str) -> str:
    key = language_key(language)
    if safety["safety_level"] == "emergency":
        if key == "spanish":
            return "Se detectaron senales de emergencia. Llame al 911 o vaya al departamento de emergencias mas cercano. CareRoute AI no es un proveedor medico."
        if key == "vietnamese":
            return "Da phat hien dau hieu cap cuu. Hay goi 911 hoac den khoa cap cuu gan nhat. CareRoute AI khong phai la nha cung cap y te."
    if safety["safety_level"] == "urgent_care_recommended":
        if key == "spanish":
            return "No se detectaron senales de emergencia, pero puede ser apropiada atencion profesional el mismo dia. Esto no reemplaza el consejo medico."
        if key == "vietnamese":
            return "Khong phat hien dau hieu cap cuu, nhung viec duoc kham trong ngay co the phu hop. Dieu nay khong thay the tu van y khoa."
    if key == "spanish":
        return "No se detectaron senales de emergencia con la informacion proporcionada. Esto no reemplaza el consejo medico."
    if key == "vietnamese":
        return "Khong phat hien dau hieu cap cuu tu thong tin da cung cap. Dieu nay khong thay the tu van y khoa."
    return safety["message"]


def localized_bundle(
    language: str,
    top: Optional[dict[str, Any]],
    safety: dict[str, Any],
    route: Optional[dict[str, Any]],
    pharmacy: Optional[dict[str, Any]],
    docs: list[str],
    call_script: str,
) -> dict[str, Any]:
    return {
        "summary": localized_summary(top, safety, language),
        "safety_message": localized_safety(safety, language),
        "steps": localized_steps(route, pharmacy, language),
        "call_script": call_script,
        "documents_needed": [translate_document(doc, language) for doc in docs],
        "disclaimer": localized_disclaimer(language),
    }


def generate_plan(profile_payload: dict[str, Any]) -> dict[str, Any]:
    profile = normalize_intake(profile_payload)
    data = load_dataset()
    safety = safety_check(profile)
    ranked = clinic_scores(profile, data)
    top = ranked[0] if ranked else None
    backup = ranked[1] if len(ranked) > 1 else None
    services = eligible_services(profile, data)
    pharmacies = pharmacy_options(profile, data)
    docs = documents_needed(top, services)
    route = top.get("transportation") if top else None
    coords = user_coordinates(profile)
    preferred_language = language_label(profile["language"])

    translations = {
        "English": localized_bundle("English", top, safety, route, pharmacies[0] if pharmacies else None, docs, build_call_script(profile, top, "English")),
        "Spanish": localized_bundle("Spanish", top, safety, route, pharmacies[0] if pharmacies else None, docs, build_call_script(profile, top, "Spanish")),
        "Vietnamese": localized_bundle("Vietnamese", top, safety, route, pharmacies[0] if pharmacies else None, docs, build_call_script(profile, top, "Vietnamese")),
    }

    return {
        "user": {**profile, **coords},
        "safety": safety,
        "summary": translations["English"]["summary"],
        "translated_summary": translations.get(preferred_language, translations["English"])["summary"],
        "insurance_verification": {
            "recommended": insurance_verification_message(profile, top),
            "backup": insurance_verification_message(profile, backup),
        },
        "recommended_clinic": top,
        "backup_clinic": backup,
        "top_options": ranked[:5],
        "documents_needed": docs,
        "city_services": services,
        "pharmacy_options": pharmacies,
        "prescription_savings": pharmacies[0] if pharmacies else None,
        "transportation": route,
        "call_script": translations["English"]["call_script"],
        "translated_call_script": translations.get(preferred_language, translations["English"])["call_script"],
        "steps": translations["English"]["steps"],
        "disclaimer": translations["English"]["disclaimer"],
        "translations": translations,
    }


def translate_text(text: str, language: str) -> str:
    key = language_key(language)
    if key == "english":
        return text
    translated = text
    for source, target in TRANSLATIONS.get(key, {}).items():
        translated = translated.replace(source, target)
    if translated == text:
        return f"[{language} translation unavailable] {text}"
    return translated


def graph_data(profile_payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    profile = normalize_intake(profile_payload or {})
    plan = generate_plan(profile)
    nodes: list[dict[str, Any]] = [
        {
            "id": profile["user_id"],
            "label": "Current user",
            "type": "user",
            "detail": f"{profile['zip_code']} | {profile['insurance_status']} | ${profile['budget']}",
            "latitude": plan["user"]["latitude"],
            "longitude": plan["user"]["longitude"],
        }
    ]
    edges: list[dict[str, Any]] = []

    for clinic in plan["top_options"][:4]:
        nodes.append(
            {
                "id": clinic["id"],
                "label": clinic["name"],
                "type": "clinic",
                "score": clinic["score"],
                "detail": clinic["estimated_cost"],
                "latitude": clinic["latitude"],
                "longitude": clinic["longitude"],
            }
        )
        edges.append({"source": profile["user_id"], "target": clinic["id"], "label": "ranked_option", "weight": clinic["score"]})
        if clinic.get("transportation"):
            route = clinic["transportation"]
            route_id = route["id"]
            if not any(node["id"] == route_id for node in nodes):
                nodes.append(
                    {
                        "id": route_id,
                        "label": route["name"],
                        "type": "transport",
                        "detail": route["route_summary"],
                    }
                )
            edges.append({"source": clinic["id"], "target": route_id, "label": "reachable_by"})

    for service in plan["city_services"][:4]:
        nodes.append(
            {
                "id": service["id"],
                "label": service["name"],
                "type": "service",
                "score": service["match_score"],
                "detail": service["category"],
            }
        )
        edges.append({"source": profile["user_id"], "target": service["id"], "label": "eligible_for", "weight": service["match_score"]})

    for pharmacy in plan["pharmacy_options"][:2]:
        nodes.append(
            {
                "id": pharmacy["id"],
                "label": pharmacy["name"],
                "type": "pharmacy",
                "score": pharmacy["score"],
                "detail": pharmacy["distance"],
                "latitude": pharmacy["latitude"],
                "longitude": pharmacy["longitude"],
            }
        )
        edges.append({"source": profile["user_id"], "target": pharmacy["id"], "label": "prescription_savings", "weight": pharmacy["score"]})

    return {"nodes": nodes, "edges": edges}


def extract_json_from_reports(response_text: str) -> Any:
    match = re.search(r"(\{.*\}|\[.*\])", response_text, re.S)
    if not match:
        return None
    return json.loads(match.group(1))
