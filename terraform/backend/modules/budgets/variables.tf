variable "project" {
  type = string
}
variable "environment" {
  type = string
}
variable "monthly_budget_usd" {
  type    = number
  default = 5
}
variable "alert_email" {
  type = string
}
