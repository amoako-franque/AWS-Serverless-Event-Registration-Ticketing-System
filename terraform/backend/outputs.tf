output "api_url" {
  description = "Base URL for the API. Share this with the frontend team."
  value       = module.api_gateway.api_endpoint
}

output "events_table_name" {
  value = module.dynamodb.events_table_name
}

output "registrations_table_name" {
  value = module.dynamodb.registrations_table_name
}

output "sns_alert_topic_arn" {
  value = module.monitoring.alerts_topic_arn
}
