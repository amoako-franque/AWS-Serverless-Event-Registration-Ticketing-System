variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "hypervisor-event-ticketing"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "alert_email" {
  type        = string
  description = "Email address for CloudWatch alarm and budget notifications"
}

variable "monthly_budget_usd" {
  type    = number
  default = 5
}

variable "frontend_origin" {
  type        = string
  description = "Origin of the teammate's frontend for CORS (e.g. https://myapp.vercel.app). Use \"*\" during development."
  default     = "*"
}
