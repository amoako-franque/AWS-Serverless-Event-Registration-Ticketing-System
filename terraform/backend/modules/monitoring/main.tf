resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts-${var.environment}"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Error rate > 5% alarm per Lambda function, using metric math
resource "aws_cloudwatch_metric_alarm" "lambda_error_rate" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-error-rate-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = 5
  alarm_description   = "Error rate exceeded 5% for ${each.value} over 5 minutes"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  metric_query {
    id          = "error_rate"
    expression  = "IF(invocations > 0, (errors / invocations) * 100, 0)"
    label       = "Error Rate (%)"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = each.value
      }
    }
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = each.value
      }
    }
  }
}

# Duration p99 alarm per function (catch slow/misbehaving functions)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-duration-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  extended_statistic  = "p99"
  threshold           = 5000 # ms
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    FunctionName = each.value
  }
}

# API Gateway 5XX error alarm
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.project}-api-5xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5xx"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    ApiId = var.api_id
  }
}
