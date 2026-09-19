from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.query_model import Region, DepthRange
from services.argo_service import get_argo_data


router = APIRouter()


# =========================================================
# REQUEST MODEL
# =========================================================

class AskRequest(BaseModel):
    question: str | None = None

    parameter: str | None = None
    region: Region | None = None
    depth: DepthRange | None = None

    # These are accepted from frontend,
    # but the demo always uses August 2026.
    start_date: str | None = None
    end_date: str | None = None


# =========================================================
# ARGO QUERY
# =========================================================

@router.post("/query")
def ask(request: AskRequest):

    # =====================================================
    # QUESTION
    # =====================================================

    question = request.question or ""

    if not question:
        question = f"Show {request.parameter or 'temperature'} data"

    question = question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    question_lower = question.lower()

    # =====================================================
    # PARAMETER
    # =====================================================

    if request.parameter:
        parameter = request.parameter.lower()

    else:
        parameter = "temperature"

        if "salinity" in question_lower:
            parameter = "salinity"

        elif "pressure" in question_lower:
            parameter = "pressure"

        elif "depth" in question_lower:
            parameter = "pressure"

    # =====================================================
    # REGION
    # =====================================================

    if request.region:

        region = request.region

    else:

        # Default: India
        region = Region(
            lat_min=5,
            lat_max=25,
            lon_min=68,
            lon_max=90
        )

        # -------------------------------------------------
        # Arabian Sea
        # -------------------------------------------------

        if "arabian sea" in question_lower:

            region = Region(
                lat_min=5,
                lat_max=25,
                lon_min=50,
                lon_max=75
            )

        # -------------------------------------------------
        # Bay of Bengal
        # -------------------------------------------------

        elif "bay of bengal" in question_lower:

            region = Region(
                lat_min=5,
                lat_max=25,
                lon_min=80,
                lon_max=100
            )

        # -------------------------------------------------
        # Indian Ocean
        # -------------------------------------------------

        elif "indian ocean" in question_lower:

            region = Region(
                lat_min=-40,
                lat_max=30,
                lon_min=20,
                lon_max=120
            )

        # -------------------------------------------------
        # India
        # -------------------------------------------------

        elif "india" in question_lower:

            region = Region(
                lat_min=5,
                lat_max=25,
                lon_min=68,
                lon_max=90
            )

    # =====================================================
    # DEPTH
    # =====================================================

    if request.depth:

        depth = request.depth

    else:

        # Default depth
        depth = DepthRange(
            min=0,
            max=2000
        )

        # 500 m
        if "500" in question_lower:

            depth = DepthRange(
                min=450,
                max=550
            )

        # 1000 m
        elif "1000" in question_lower:

            depth = DepthRange(
                min=950,
                max=1050
            )

    # =====================================================
    # DATE
    # =====================================================
    # IMPORTANT:
    # ONLY AUGUST 2026
    # =====================================================

    start_date = "2026-08-01"
    end_date = "2026-08-31"

    # =====================================================
    # LOG QUERY
    # =====================================================

    print("\n========================================")
    print("ARGO QUERY")
    print("========================================")
    print("Question:", question)
    print("Parameter:", parameter)
    print("Region:", region.model_dump())
    print("Depth:", depth.model_dump())
    print("Start date:", start_date)
    print("End date:", end_date)
    print("========================================\n")

    # =====================================================
    # CALL ARGO SERVICE
    # =====================================================

    try:

        result = get_argo_data(
            parameter,
            region,
            depth,
            start_date,
            end_date
        )

    except Exception as error:

        print("ARGO service error:", error)

        raise HTTPException(
            status_code=500,
            detail=f"ARGO service error: {str(error)}"
        )

    # =====================================================
    # EXTRACT OBSERVATIONS
    # =====================================================

    observations = result.get("data", [])

    if observations is None:
        observations = []

    if not isinstance(observations, list):
        observations = []

    # =====================================================
    # CALCULATE STATISTICS
    # =====================================================

    valid_values = []

    for observation in observations:

        if parameter == "temperature":

            value = observation.get("temperature")

        elif parameter == "salinity":

            value = observation.get("salinity")

        else:

            value = observation.get("pressure")

        if value is not None:

            try:
                valid_values.append(float(value))

            except (TypeError, ValueError):
                pass

    # =====================================================
    # STATISTICS
    # =====================================================

    if valid_values:

        average = round(
            sum(valid_values) / len(valid_values),
            2
        )

        minimum = round(
            min(valid_values),
            2
        )

        maximum = round(
            max(valid_values),
            2
        )

    else:

        average = None
        minimum = None
        maximum = None

    # =====================================================
    # CHART DATA
    # =====================================================
    # Send maximum 100 points to frontend.
    # This prevents the browser from processing
    # thousands of graph points.
    # =====================================================

    chart = []

    if len(observations) > 100:

        step = len(observations) / 100

        chart_source = [
            observations[int(i * step)]
            for i in range(100)
        ]

    else:

        chart_source = observations

    for observation in chart_source:

        if parameter == "temperature":

            value = observation.get("temperature")

        elif parameter == "salinity":

            value = observation.get("salinity")

        else:

            value = observation.get("pressure")

        if value is not None:

            try:

                chart.append({
                    "value": float(value)
                })

            except (TypeError, ValueError):

                pass

    # =====================================================
    # FIRST RESULT
    # =====================================================

    first_result = (
        observations[0]
        if observations
        else {}
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "success": True,

        "title": (
            f"ARGO {parameter.title()} Observation"
        ),

        "summary": (
            f"Retrieved {len(observations)} ARGO "
            f"observations for {parameter} from "
            f"{start_date} to {end_date}."
        ),

        "text": (
            f"Retrieved {len(observations)} ARGO "
            f"observations for August 2026."
        ),

        "question": question,

        # =================================================
        # QUERY
        # =================================================

        "query": {

            "parameter": parameter,

            "region": region.model_dump(),

            "depth": depth.model_dump(),

            "start_date": start_date,

            "end_date": end_date
        },

        # =================================================
        # STATISTICS
        # =================================================

        "statistics": {

            "valid_observations": len(valid_values),

            "average": average,

            "minimum": minimum,

            "maximum": maximum
        },

        # =================================================
        # COUNTS
        # =================================================

        "total_observations": len(observations),

        "observations": len(observations),

        # =================================================
        # DATA
        # =================================================

        "data": observations,

        # =================================================
        # FIRST RESULT
        # =================================================

        "result": first_result,

        # =================================================
        # GRAPH
        # =================================================

        "chart": chart,

        # =================================================
        # DATE RANGE
        # =================================================

        "date_range": (
            f"{start_date} → {end_date}"
        ),

        # =================================================
        # SOURCE
        # =================================================

        "data_source": "ARGO",

        "source": "ARGO",

        "live": True
    }