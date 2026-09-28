def urgent_response(red_flag):
    return {
        "status": "URGENT",
        "flag": red_flag["flag"],
        "severity": red_flag["severity"],
        "action": red_flag["action"],
        "message": red_flag["message"],
        "disclaimer": "This tool does not provide medical diagnoses. Seek appropriate medical care."
    }