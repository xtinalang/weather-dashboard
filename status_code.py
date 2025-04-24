/**
 * Handles HTTP errors based on status codes
 * @param {number} statusCode - The HTTP status code
 * @param {string} message - Optional custom error message
 * @returns {Object} Error response object with appropriate details
 */
function handleHttpError(statusCode, message = '') {
  // Define standard HTTP error categories and messages
  const errorResponses = {
    // 4xx Client Errors
    400: { title: 'Bad Request', description: 'The request could not be understood or was missing required parameters.' },
    401: { title: 'Unauthorized', description: 'Authentication required and has failed or not been provided.' },
    402: { title: 'Payment Required', description: 'Reserved for future use.' },
    403: { title: 'Forbidden', description: 'Server understood the request but refuses to authorize it.' },
    404: { title: 'Not Found', description: 'The requested resource could not be found.' },
    405: { title: 'Method Not Allowed', description: 'The request method is not supported for the requested resource.' },
    406: { title: 'Not Acceptable', description: 'The requested resource is capable of generating only content not acceptable according to the Accept headers sent.' },
    407: { title: 'Proxy Authentication Required', description: 'Authentication with proxy required.' },
    408: { title: 'Request Timeout', description: 'The server timed out waiting for the request.' },
    409: { title: 'Conflict', description: 'The request could not be completed due to a conflict with the current state of the resource.' },
    410: { title: 'Gone', description: 'The requested resource is no longer available and will not be available again.' },
    411: { title: 'Length Required', description: 'The request did not specify the length of its content.' },
    412: { title: 'Precondition Failed', description: 'The server does not meet one of the preconditions specified in the request.' },
    413: { title: 'Payload Too Large', description: 'The request is larger than the server is willing or able to process.' },
    414: { title: 'URI Too Long', description: 'The URI provided was too long for the server to process.' },
    415: { title: 'Unsupported Media Type', description: 'The request entity has a media type which the server or resource does not support.' },
    416: { title: 'Range Not Satisfiable', description: 'The client has asked for a portion of the file, but the server cannot supply that portion.' },
    417: { title: 'Expectation Failed', description: 'The server cannot meet the requirements of the Expect request-header field.' },
    418: { title: 'I\'m a teapot', description: 'The server refuses the attempt to brew coffee with a teapot.' },
    421: { title: 'Misdirected Request', description: 'The request was directed at a server that is not able to produce a response.' },
    422: { title: 'Unprocessable Entity', description: 'The request was well-formed but was unable to be followed due to semantic errors.' },
    423: { title: 'Locked', description: 'The resource that is being accessed is locked.' },
    424: { title: 'Failed Dependency', description: 'The request failed due to failure of a previous request.' },
    425: { title: 'Too Early', description: 'The server is unwilling to risk processing a request that might be replayed.' },
    426: { title: 'Upgrade Required', description: 'The client should switch to a different protocol.' },
    428: { title: 'Precondition Required', description: 'The origin server requires the request to be conditional.' },
    429: { title: 'Too Many Requests', description: 'The user has sent too many requests in a given amount of time.' },
    431: { title: 'Request Header Fields Too Large', description: 'The server is unwilling to process the request because either an individual header field, or all the header fields collectively, are too large.' },
    451: { title: 'Unavailable For Legal Reasons', description: 'The server is denying access to the resource as a consequence of a legal demand.' },
    
    // 5xx Server Errors
    500: { title: 'Internal Server Error', description: 'The server encountered an unexpected condition that prevented it from fulfilling the request.' },
    501: { title: 'Not Implemented', description: 'The server does not support the functionality required to fulfill the request.' },
    502: { title: 'Bad Gateway', description: 'The server received an invalid response from the upstream server.' },
    503: { title: 'Service Unavailable', description: 'The server is currently unavailable (because it is overloaded or down for maintenance).' },
    504: { title: 'Gateway Timeout', description: 'The server was acting as a gateway or proxy and did not receive a timely response from the upstream server.' },
    505: { title: 'HTTP Version Not Supported', description: 'The server does not support the HTTP protocol version used in the request.' },
    506: { title: 'Variant Also Negotiates', description: 'Transparent content negotiation for the request results in a circular reference.' },
    507: { title: 'Insufficient Storage', description: 'The server is unable to store the representation needed to complete the request.' },
    508: { title: 'Loop Detected', description: 'The server detected an infinite loop while processing the request.' },
    510: { title: 'Not Extended', description: 'Further extensions to the request are required for the server to fulfill it.' },
    511: { title: 'Network Authentication Required', description: 'The client needs to authenticate to gain network access.' }
  };

  // Determine error category (client or server error)
  const errorCategory = statusCode >= 500 ? 'Server Error' : 'Client Error';
  
  // Get the error details or use a generic error message if not found
  const errorDetails = errorResponses[statusCode] || { 
    title: 'Unknown Error', 
    description: 'An unknown error occurred.' 
  };
  
  // Create the error response
  const errorResponse = {
    error: {
      statusCode,
      category: errorCategory,
      title: errorDetails.title,
      description: message || errorDetails.description
    }
  };
  
  return errorResponse;
}

// Example usage:
function handleApiResponse(response) {
  if (!response.ok) {
    const errorDetails = handleHttpError(response.status);
    console.error(`Error ${response.status}: ${errorDetails.error.title}`);
    return errorDetails;
  }
  return response.json();
}
