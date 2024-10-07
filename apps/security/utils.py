def extract_device_info(request):
    return {
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        "ip_address": request.META.get("REMOTE_ADDR", ""),
    }
