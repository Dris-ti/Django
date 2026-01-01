from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings

class BotDetectionMiddleware:
    """
    Middleware for heuristic-based bot detection and request scoring.

    @description
    Evaluates incoming HTTP requests against common bot signatures, missing browser-standard 
    headers, and IP-based rate limits. Instead of immediate rejection, it assigns a 'risk score'. 
    If the cumulative score meets or exceeds the `BLOCK_THRESHOLD`, the request is rejected with a 403 Forbidden.

    @initialization
    :param get_response: The next link in the Django middleware chain.
    :attr developer_mode: Boolean from settings.BOT_DETECTION_DEV_MODE to bypass checks during development.

    @returns
    - HTTP 403 JsonResponse if bot score >= threshold.
    - Standard HttpResponse if score < threshold.

    @example
    # Request from a standard browser: Score 0 -> Allowed.
    # Request from Python Requests (no headers): 
    #   +3 (Suspicious UA) + 4 (Missing Sec-Fetch headers) = Score 7 -> Blocked.

    @input_arguments
    - SUSPICIOUS_UA_KEYWORDS: List of strings to match against the User-Agent.
    - REQUIRED_BROWSER_HEADERS: Django META keys for Sec-Fetch and Language headers.
    - BLOCK_THRESHOLD: Integer (Default 4).

    @possible_input_values
    - settings.BOT_DETECTION_DEV_MODE: True | False
    - cache.get(key): Integer or None (Internal rate limiting)
    """

    SUSPICIOUS_UA_KEYWORDS = [
        "postman", "curl", "wget", "python", "requests",
        "httpclient", "scrapy", "bot", "spider", "crawler"
    ]

    # These headers are sent by virtually all modern browsers (Chrome, Firefox, Safari)
    REQUIRED_BROWSER_HEADERS = [
        "HTTP_ACCEPT_LANGUAGE",
        "HTTP_SEC_FETCH_SITE",
        "HTTP_SEC_FETCH_MODE",
        "HTTP_SEC_FETCH_DEST",
    ]

    BLOCK_THRESHOLD = 4

    def __init__(self, get_response):
        self.get_response = get_response
        self.developer_mode = getattr(settings, "BOT_DETECTION_DEV_MODE", False)

    def __call__(self, request):
        """
        Main middleware entry point.
        """
        if self.developer_mode:
            return self.get_response(request)
        
        score, reasons = self.calculate_score(request)

        if score >= self.BLOCK_THRESHOLD:
            return JsonResponse(
                {
                    "error": "Suspicious activity detected",
                    "score": score,
                    "reason": reasons
                },
                status=403
            )

        return self.get_response(request)

    def calculate_score(self, request):
        """
        Heuristic engine to calculate bot risk.
        :returns: tuple (int: score, list: reasons)
        """
        score = 0
        reasons = []

        # 1. User-Agent Analysis
        ua = request.META.get("HTTP_USER_AGENT", "").lower()
        if not ua:
            score += 2
            reasons.append("Missing User-Agent")
        elif any(k in ua for k in self.SUSPICIOUS_UA_KEYWORDS):
            score += 3
            reasons.append(f"Suspicious User-Agent: {ua}")

        # 2. Sec-Fetch & Browser Integrity Check
        # Most bots/crawlers don't spoof these specific metadata headers
        missing_headers = [
            h for h in self.REQUIRED_BROWSER_HEADERS
            if h not in request.META
        ]
        if missing_headers:
            score += len(missing_headers)
            reasons.append(f"Missing browser-integrity headers: {', '.join(missing_headers)}")

        # 3. Navigation Context
        if not request.META.get("HTTP_REFERER"):
            score += 1
            reasons.append("Missing Referer header")

        # 4. Behavioral Analysis (Rate Limiting)
        ip = self.get_client_ip(request)
        if ip and self.is_rate_limited(ip):
            score += 2
            reasons.append(f"Rate limit exceeded for IP: {ip}")

        return score, reasons

    def get_client_ip(self, request):
        """
        Extracts the real client IP, considering potential Proxy/Load Balancer headers.
        """
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def is_rate_limited(self, ip):
        """
        Checks cache to see if IP has exceeded the 60 requests/min threshold.
        """
        key = f"bot:rate:{ip}"
        current = cache.get(key)

        if current is None:
            cache.set(key, 1, timeout=60)
            return False

        if current > 60:
            return True

        try:
            cache.incr(key)
        except ValueError:
            # Fallback if key expired between get and incr
            cache.set(key, 1, timeout=60)
            
        return False