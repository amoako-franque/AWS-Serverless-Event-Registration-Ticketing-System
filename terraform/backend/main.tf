locals {
  build_dir = "${path.module}/../../backend/build"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

module "dynamodb" {
  source      = "./modules/dynamodb"
  project     = var.project
  environment = var.environment
}

# ---- POST /register ----
module "lambda_register" {
  source        = "./modules/lambda"
  function_name = "${var.project}-register-${var.environment}"
  zip_path      = "${local.build_dir}/register.zip"
  handler       = "handler.handler"
  tags          = local.common_tags

  environment_variables = {
    EVENTS_TABLE        = module.dynamodb.events_table_name
    REGISTRATIONS_TABLE = module.dynamodb.registrations_table_name
  }

  iam_policy_statements = [
    {
      actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
      resources = [module.dynamodb.events_table_arn]
    },
    {
      actions   = ["dynamodb:PutItem"]
      resources = [module.dynamodb.registrations_table_arn]
    },
  ]
}

# ---- GET /events ----
module "lambda_list_events" {
  source        = "./modules/lambda"
  function_name = "${var.project}-list-events-${var.environment}"
  zip_path      = "${local.build_dir}/list_events.zip"
  handler       = "handler.handler"
  tags          = local.common_tags

  environment_variables = {
    EVENTS_TABLE = module.dynamodb.events_table_name
  }

  iam_policy_statements = [
    {
      actions   = ["dynamodb:Scan"]
      resources = [module.dynamodb.events_table_arn]
    },
  ]
}

# ---- GET /registrations/{email} ----
module "lambda_get_registrations" {
  source        = "./modules/lambda"
  function_name = "${var.project}-get-registrations-${var.environment}"
  zip_path      = "${local.build_dir}/get_registrations.zip"
  handler       = "handler.handler"
  tags          = local.common_tags

  environment_variables = {
    REGISTRATIONS_TABLE = module.dynamodb.registrations_table_name
  }

  iam_policy_statements = [
    {
      actions   = ["dynamodb:Query"]
      resources = [
        module.dynamodb.registrations_table_arn,
        "${module.dynamodb.registrations_table_arn}/index/emailIndex",
      ]
    },
  ]
}

# ---- DELETE /registration/{id} ----
module "lambda_cancel_registration" {
  source        = "./modules/lambda"
  function_name = "${var.project}-cancel-registration-${var.environment}"
  zip_path      = "${local.build_dir}/cancel_registration.zip"
  handler       = "handler.handler"
  tags          = local.common_tags

  environment_variables = {
    EVENTS_TABLE        = module.dynamodb.events_table_name
    REGISTRATIONS_TABLE = module.dynamodb.registrations_table_name
  }

  iam_policy_statements = [
    {
      actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
      resources = [module.dynamodb.registrations_table_arn]
    },
    {
      actions   = ["dynamodb:UpdateItem"]
      resources = [module.dynamodb.events_table_arn]
    },
  ]
}

module "api_gateway" {
  source      = "./modules/api-gateway"
  project     = var.project
  environment = var.environment

  register_lambda_invoke_arn    = module.lambda_register.invoke_arn
  register_lambda_function_name = module.lambda_register.function_name

  list_events_lambda_invoke_arn    = module.lambda_list_events.invoke_arn
  list_events_lambda_function_name = module.lambda_list_events.function_name

  get_registrations_lambda_invoke_arn    = module.lambda_get_registrations.invoke_arn
  get_registrations_lambda_function_name = module.lambda_get_registrations.function_name

  cancel_registration_lambda_invoke_arn    = module.lambda_cancel_registration.invoke_arn
  cancel_registration_lambda_function_name = module.lambda_cancel_registration.function_name

  cors_allow_origin = var.frontend_origin
}

module "monitoring" {
  source      = "./modules/monitoring"
  project     = var.project
  environment = var.environment
  alert_email = var.alert_email
  api_id      = module.api_gateway.api_id

  lambda_function_names = [
    module.lambda_register.function_name,
    module.lambda_list_events.function_name,
    module.lambda_get_registrations.function_name,
    module.lambda_cancel_registration.function_name,
  ]
}

module "budgets" {
  source             = "./modules/budgets"
  project            = var.project
  environment        = var.environment
  alert_email        = var.alert_email
  monthly_budget_usd = var.monthly_budget_usd
}
