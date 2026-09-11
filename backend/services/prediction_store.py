import json
from sqlalchemy.orm import Session
from app.database.models import PredictionResult
from app.core.logs import logger


def save_prediction(
    db: Session,
    patient_id: int,
    prediction_type: str,
    result: dict,
    input_data: dict = None
) -> PredictionResult:
    """
    Save any ML prediction result linked to a patient.

    Args:
        db:              SQLAlchemy session
        patient_id:      Patient DB id
        prediction_type: "diabetes" | "heart" | "xray"
        result:          Dict returned by the prediction service
        input_data:      Original input fields (optional, stored as JSON)
    """
    record = PredictionResult(
        patient_id=patient_id,
        prediction_type=prediction_type,
        probability=result.get("probability") or result.get("confidence"),
        risk_level=result.get("risk_level") or result.get("disease"),
        input_data=json.dumps(input_data) if input_data else None,
        result_summary=json.dumps(result),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Prediction saved | type={prediction_type} | patient={patient_id} | risk={record.risk_level}")
    return record
