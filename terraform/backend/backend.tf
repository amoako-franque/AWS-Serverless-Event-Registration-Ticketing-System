terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Bootstrap this backend first (S3 bucket + DynamoDB lock table)
  # via a one-time manual apply, then uncomment:

  backend "s3" {
    bucket         = "event-ticketing-tfstate-be-04"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "event-ticketing-be-tf-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
