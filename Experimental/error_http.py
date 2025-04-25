http_error_message = lambda code: {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    500: "Internal Server Error"
}.get(code, "Unknown Error")

print(http_error_message(404))  # Not Found
print(http_error_message(999))  # Unknown Error