import logging

from backend.safety.red_flags import check_red_flags
from backend.safety.safety_response import urgent_response


logger = logging.getLogger(__name__)


def safety_gate1(patient):
    red_flag = check_red_flags(patient)

    if red_flag:
        logger.warning(
            "Safety Gate 1 triggered: %s",
            red_flag["flag"]
        )

        response = urgent_response(red_flag)
        response["safe_to_continue"] = False
        return response

    return {
        "no_red_flags": True,
        "safe_to_continue": True
    }