# Using API Gateway v2 (HTTP API) - cheaper and simpler than REST API (v1)
# for a straightforward Lambda-proxy setup like this one.
#
# Every route below follows the same 3-resource pattern:
#   1. aws_apigatewayv2_integration - tells API Gateway which Lambda to
#      call and how to format the request (AWS_PROXY passes the raw
#      HTTP request through, letting the Lambda handle parsing itself)
#   2. aws_apigatewayv2_route       - maps an HTTP method + path to that
#      integration (e.g. "POST /register")
#   3. aws_lambda_permission        - grants API Gateway permission to
#      actually invoke that specific Lambda function; without this,
#      the route exists but every call returns a 500 Internal Server
#      Error since Lambda rejects the invocation

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.project}-api-${var.environment}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = [var.cors_allow_origin]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type"]
  }
}

resource "aws_apigatewayv2_stage" "this" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project}-${var.environment}"
  retention_in_days = 14
}

# ---- POST /register ----
resource "aws_apigatewayv2_integration" "register" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.register_lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "register" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /register"
  target    = "integrations/${aws_apigatewayv2_integration.register.id}"
}

resource "aws_lambda_permission" "register" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.register_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# ---- GET /events ----
resource "aws_apigatewayv2_integration" "list_events" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.list_events_lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "list_events" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /events"
  target    = "integrations/${aws_apigatewayv2_integration.list_events.id}"
}

resource "aws_lambda_permission" "list_events" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.list_events_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# ---- GET /registrations/{email} ----
resource "aws_apigatewayv2_integration" "get_registrations" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.get_registrations_lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "get_registrations" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "GET /registrations/{email}"
  target    = "integrations/${aws_apigatewayv2_integration.get_registrations.id}"
}

resource "aws_lambda_permission" "get_registrations" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.get_registrations_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# ---- DELETE /registration/{id} ----
resource "aws_apigatewayv2_integration" "cancel_registration" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.cancel_registration_lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "cancel_registration" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "DELETE /registration/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.cancel_registration.id}"
}

resource "aws_lambda_permission" "cancel_registration" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.cancel_registration_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# ---- POST /events ----
# Note: this shares the /events PATH with "GET /events" above, but HTTP
# API routes key on method+path together, so "GET /events" and
# "POST /events" are entirely separate routes pointing at different
# Lambdas - no conflict.
resource "aws_apigatewayv2_integration" "create_event" {
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.create_event_lambda_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "create_event" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /events"
  target    = "integrations/${aws_apigatewayv2_integration.create_event.id}"
}

resource "aws_lambda_permission" "create_event" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.create_event_lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}