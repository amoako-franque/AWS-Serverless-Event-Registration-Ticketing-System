variable "project" {
  type = string
}
variable "environment" {
  type = string
}
variable "lambda_function_names" {
  type = list(string)
}
variable "api_id" {
  type = string
}
variable "alert_email" {
  type        = string
  description = "Email to receive SNS alarm and budget notifications"
}
variable "monthly_budget_usd" {
  type    = number
  default = 5
}
