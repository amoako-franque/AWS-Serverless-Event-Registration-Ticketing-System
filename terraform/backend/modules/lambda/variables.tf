variable "function_name" {
  type        = string
  description = "Full Lambda function name"
}

variable "zip_path" {
  type        = string
  description = "Path to the pre-built deployment zip for this function"
}

variable "handler" {
  type    = string
  default = "handler.handler"
}

variable "runtime" {
  type    = string
  default = "python3.12"
}

variable "timeout" {
  type    = number
  default = 10
}

variable "memory_size" {
  type    = number
  default = 128
}

variable "environment_variables" {
  type    = map(string)
  default = {}
}

variable "iam_policy_statements" {
  description = "List of least-privilege IAM policy statements this function needs"
  type = list(object({
    actions   = list(string)
    resources = list(string)
  }))
  default = []
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "tags" {
  type    = map(string)
  default = {}
}
