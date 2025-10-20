# core/middleware/empty_to_null.py
import json

class EmptyToNullMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.content_type == "application/json":
            try:
                body_unicode = request.body.decode("utf-8")
                if body_unicode.strip():
                    data = json.loads(body_unicode)

                    def replace_empty(d):
                        if isinstance(d, dict):
                            return {k: replace_empty(v) for k, v in d.items()}
                        elif isinstance(d, list):
                            return [replace_empty(i) for i in d]
                        elif d == "":
                            return None
                        return d

                    data = replace_empty(data)
                    request._body = json.dumps(data).encode("utf-8")
            except Exception:
                pass

        return self.get_response(request)