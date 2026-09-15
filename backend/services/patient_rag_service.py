import json
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.models import User, Patient, Visit, Medication, PredictionResult
from app.core.logs import logger


class PatientRAGResult(BaseModel):
    context_text: str
    sources: List[Dict[str, Any]]
    has_records: bool
    record_types_found: List[str]


class PatientRAGService:
    """
    Dedicated RAG service for retrieving and contextualizing confidential patient records.
    Enforces strict tenant isolation: records are queried ONLY for the authenticated patient_id.
    """

    def retrieve_patient_context(
        self,
        patient_id: int,
        db: Session,
        query: Optional[str] = None
    ) -> PatientRAGResult:
        """
        Retrieve structured medical records for the authenticated patient.
        Never queries or returns records across different patients.
        """
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            logger.info(f"PatientRAG: No patient profile found for patient_id={patient_id}")
            return PatientRAGResult(
                context_text="",
                sources=[],
                has_records=False,
                record_types_found=[]
            )

        context_blocks: List[str] = []
        sources: List[Dict[str, Any]] = []
        record_types_found: List[str] = []

        # 1. Demographics & Baseline Clinical Profile
        demo_parts = []
        if patient.user and patient.user.full_name:
            demo_parts.append(f"Name: {patient.user.full_name}")
        if patient.gender:
            gender_val = patient.gender.value if hasattr(patient.gender, 'value') else str(patient.gender)
            demo_parts.append(f"Gender: {gender_val}")
        if patient.date_of_birth:
            demo_parts.append(f"DOB: {patient.date_of_birth}")
        if patient.blood_group:
            bg_val = patient.blood_group.value if hasattr(patient.blood_group, 'value') else str(patient.blood_group)
            demo_parts.append(f"Blood Group: {bg_val}")
        if patient.allergies:
            demo_parts.append(f"Known Allergies: {patient.allergies}")
        else:
            demo_parts.append("Known Allergies: None recorded")

        if demo_parts:
            context_blocks.append("[PATIENT CLINICAL PROFILE]\n" + " | ".join(demo_parts))
            record_types_found.append("demographics")
            sources.append({
                "document_title": "Patient Clinical Profile",
                "section": "Demographics & Allergies",
                "snippet": " | ".join(demo_parts)
            })

        # 2. Prescriptions & Medications (strictly filtered by patient_id)
        meds = db.query(Medication).filter(
            Medication.patient_id == patient.id
        ).order_by(Medication.prescribed_at.desc()).all()

        if meds:
            med_lines = []
            for m in meds:
                status = "ACTIVE" if m.is_active else "DISCONTINUED / COMPLETED"
                details = [f"Medication: {m.name}"]
                if m.dosage:
                    details.append(f"Dosage: {m.dosage}")
                if m.frequency:
                    details.append(f"Frequency: {m.frequency}")
                if m.duration:
                    details.append(f"Duration: {m.duration}")
                if m.prescribed_by:
                    details.append(f"Prescribed by: {m.prescribed_by}")
                if m.notes:
                    details.append(f"Notes: {m.notes}")
                details.append(f"Status: {status}")
                med_lines.append(" - " + ", ".join(details))

            context_blocks.append("[MEDICATION & PRESCRIPTION HISTORY]\n" + "\n".join(med_lines))
            record_types_found.append("medications")
            sources.append({
                "document_title": "Medication Records",
                "section": f"{len(meds)} Prescriptions Recorded",
                "snippet": f"{len(meds)} medication(s) found in patient record."
            })

        # 3. Doctor Consultations & Visits (strictly filtered by patient_id)
        visits = db.query(Visit).filter(
            Visit.patient_id == patient.id
        ).order_by(Visit.visit_date.desc()).all()

        if visits:
            visit_lines = []
            for v in visits:
                date_str = v.visit_date.strftime("%Y-%m-%d") if v.visit_date else "Unknown Date"
                doc_name = v.doctor.user.full_name if (v.doctor and v.doctor.user) else "Doctor"
                v_details = [f"Date: {date_str}", f"Doctor: {doc_name}"]
                if v.chief_complaint:
                    v_details.append(f"Chief Complaint: {v.chief_complaint}")
                if v.diagnosis:
                    v_details.append(f"Diagnosis: {v.diagnosis}")
                if v.notes:
                    v_details.append(f"Clinical Notes: {v.notes}")
                if v.follow_up_date:
                    v_details.append(f"Follow-up: {v.follow_up_date}")
                visit_lines.append(" - " + " | ".join(v_details))

            context_blocks.append("[CLINICAL VISITS & CONSULTATION NOTES]\n" + "\n".join(visit_lines))
            record_types_found.append("visits")
            sources.append({
                "document_title": "Clinical Visits & Consultations",
                "section": f"{len(visits)} Visits Recorded",
                "snippet": f"{len(visits)} consultation visit(s) found in record."
            })

        # 4. Diagnostic Lab Results & ML Predictions (strictly filtered by patient_id)
        predictions = db.query(PredictionResult).filter(
            PredictionResult.patient_id == patient.id
        ).order_by(PredictionResult.created_at.desc()).all()

        if predictions:
            pred_lines = []
            for p in predictions:
                date_str = p.created_at.strftime("%Y-%m-%d") if p.created_at else "Recent"
                p_type = p.prediction_type.upper()
                line = f" - Date: {date_str} | Test/Report Type: {p_type} | Risk/Result: {p.risk_level or 'N/A'}"
                if p.probability is not None:
                    line += f" (Confidence/Probability: {round(p.probability * 100, 1)}%)"

                # Parse detailed lab inputs if available (e.g. HbA1c, Glucose, BP)
                if p.input_data:
                    try:
                        inputs = json.loads(p.input_data)
                        if isinstance(inputs, dict):
                            input_details = []
                            for k, v in inputs.items():
                                input_details.append(f"{k}: {v}")
                            if input_details:
                                line += f" | Measured Parameters: [{', '.join(input_details)}]"
                    except Exception:
                        pass

                if p.result_summary:
                    try:
                        summary_obj = json.loads(p.result_summary)
                        if isinstance(summary_obj, dict):
                            rec_text = summary_obj.get("recommendation") or summary_obj.get("message")
                            if rec_text:
                                line += f" | Recommendation: {rec_text}"
                    except Exception:
                        pass

                pred_lines.append(line)

            context_blocks.append("[DIAGNOSTIC LAB REPORTS & PREDICTIONS]\n" + "\n".join(pred_lines))
            record_types_found.append("predictions")
            sources.append({
                "document_title": "Diagnostic Reports & Test Results",
                "section": f"{len(predictions)} Diagnostic Reports Recorded",
                "snippet": f"{len(predictions)} report(s) found in record."
            })

        has_records = len(context_blocks) > 0
        full_context = "\n\n".join(context_blocks)

        logger.info(
            f"PatientRAG: Retrieved context for patient_id={patient_id} | "
            f"record_types={record_types_found} | total_sources={len(sources)}"
        )

        return PatientRAGResult(
            context_text=full_context,
            sources=sources,
            has_records=has_records,
            record_types_found=record_types_found
        )


_patient_rag_instance: Optional[PatientRAGService] = None


def get_patient_rag_service() -> PatientRAGService:
    global _patient_rag_instance
    if _patient_rag_instance is None:
        _patient_rag_instance = PatientRAGService()
    return _patient_rag_instance
