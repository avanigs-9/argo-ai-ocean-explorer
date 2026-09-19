import requests
from datetime import datetime, timedelta


ARGO_URL = "https://argovis-api.colorado.edu/argo"


def fetch_argo_chunk(
    parameter,
    region,
    depth,
    start_date,
    end_date
):
    """
    Fetch one smaller time period from Argovis.
    """

    params = [
        ("data", "pressure"),
        ("data", "temperature"),
        ("data", "salinity"),

        (
            "box",
            f"[[{region.lon_min},{region.lat_min}],"
            f"[{region.lon_max},{region.lat_max}]]"
        ),

        ("startDate", f"{start_date}T00:00:00Z"),
        ("endDate", f"{end_date}T23:59:59Z"),
    ]

    response = requests.get(
        ARGO_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()

    return response.json()


def get_argo_data(
    parameter,
    region,
    depth,
    start_date,
    end_date
):

    all_observations = []

    # =========================================================
    # CONVERT DATE STRINGS TO datetime OBJECTS
    # =========================================================

    if isinstance(start_date, str):
        start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        )

    if isinstance(end_date, str):
        end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        )
    current_date = start_date
    final_date = end_date

    # =========================================================
    # FETCH DATA IN SMALL CHUNKS
    # =========================================================

    while current_date <= final_date:

        chunk_end = min(
            current_date + timedelta(days=29),
            final_date
        )

        chunk_start_str = current_date.strftime(
            "%Y-%m-%d"
        )

        chunk_end_str = chunk_end.strftime(
            "%Y-%m-%d"
        )

        print(
            f"Fetching ARGO data: "
            f"{chunk_start_str} → {chunk_end_str}"
        )

        try:

            raw_data = fetch_argo_chunk(
                parameter,
                region,
                depth,
                chunk_start_str,
                chunk_end_str
            )

        except requests.RequestException as error:

            print(
                "ARGO request failed:",
                error
            )

            current_date = (
                chunk_end +
                timedelta(days=1)
            )

            continue

        # =====================================================
        # CHECK RESPONSE
        # =====================================================

        if not isinstance(raw_data, list):

            print(
                "Unexpected ARGO response format"
            )

            current_date = (
                chunk_end +
                timedelta(days=1)
            )

            continue

        # =====================================================
        # PROCESS PROFILES
        # =====================================================

        for profile in raw_data:

            try:

                coordinates = (
                    profile["geolocation"]
                    ["coordinates"]
                )

                longitude = coordinates[0]
                latitude = coordinates[1]

                timestamp = profile.get(
                    "timestamp"
                )

                data = profile.get(
                    "data"
                )

                if not data or len(data) < 3:
                    continue

                # Argovis structure:
                #
                # data[0] = pressure
                # data[1] = temperature
                # data[2] = salinity

                pressures = data[0]
                temperatures = data[1]
                salinities = data[2]

                number_of_levels = len(
                    pressures
                )

                # =================================================
                # PROCESS EACH DEPTH LEVEL
                # =================================================

                for i in range(
                    number_of_levels
                ):

                    pressure_value = (
                        pressures[i]
                    )

                    if pressure_value is None:
                        continue

                    # Check requested depth range

                    if (
                        pressure_value < depth.min
                        or
                        pressure_value > depth.max
                    ):
                        continue

                    # Temperature

                    temperature_value = (
                        temperatures[i]
                        if i < len(temperatures)
                        else None
                    )

                    # Salinity

                    salinity_value = (
                        salinities[i]
                        if i < len(salinities)
                        else None
                    )

                    # =================================================
                    # CREATE OBSERVATION
                    # =================================================

                    observation = {
                        "latitude": latitude,
                        "longitude": longitude,
                        "date": timestamp,
                        "pressure": pressure_value
                    }

                    if parameter == "temperature":

                        observation[
                            "temperature"
                        ] = temperature_value

                    elif parameter == "salinity":

                        observation[
                            "salinity"
                        ] = salinity_value

                    elif parameter == "pressure":

                        pass

                    else:

                        continue

                    all_observations.append(
                        observation
                    )

            except (
                KeyError,
                IndexError,
                TypeError,
                ValueError
            ) as error:

                print(
                    "Skipping invalid ARGO profile:",
                    error
                )

        # =====================================================
        # MOVE TO NEXT CHUNK
        # =====================================================

        current_date = (
            chunk_end +
            timedelta(days=1)
        )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    print(
        "FINAL OBSERVATION COUNT:",
        len(all_observations)
    )

    if not all_observations:

        return {
            "success": True,
            "data": [],
            "message": (
                "No ARGO data found "
                "for the specified query."
            )
        }

    return {
        "success": True,
        "data": all_observations
    }