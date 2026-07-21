resource "aws_dynamodb_table" "events" {
  name         = "${var.project}-events-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "eventId"

  attribute {
    name = "eventId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "registrations" {
  name         = "${var.project}-registrations-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "registrationId"

  attribute {
    name = "registrationId"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "registeredAt"
    type = "S"
  }

  attribute {
    name = "eventId"
    type = "S"
  }

  global_secondary_index {
    name            = "emailIndex"
    hash_key        = "email"
    range_key       = "registeredAt"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "eventIndex"
    hash_key        = "eventId"
    range_key       = "registeredAt"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}
