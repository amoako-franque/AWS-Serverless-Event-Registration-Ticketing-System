variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "register_lambda_invoke_arn" {
  type = string
}
variable "register_lambda_function_name" {
  type = string
}

variable "list_events_lambda_invoke_arn" {
  type = string
}
variable "list_events_lambda_function_name" {
  type = string
}

variable "get_registrations_lambda_invoke_arn" {
  type = string
}
variable "get_registrations_lambda_function_name" {
  type = string
}

variable "cancel_registration_lambda_invoke_arn" {
  type = string
}
variable "cancel_registration_lambda_function_name" {
  type = string
}

variable "cors_allow_origin" {
  type    = string
  default = "*"
}
