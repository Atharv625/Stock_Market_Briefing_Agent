terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "lambda_arn" {
  type = string
}

resource "aws_scheduler_schedule" "pre_market" {
  name       = "stock-agent-pre-market"
  group_name = "default"
  flexible_time_window { mode = "OFF" }
  schedule_expression          = "cron(30 2 ? * MON-FRI *)"
  schedule_expression_timezone = "UTC"
  target {
    arn      = var.lambda_arn
    role_arn = aws_iam_role.scheduler_role.arn
    input    = jsonencode({ report_type = "pre_market" })
  }
}

resource "aws_iam_role" "scheduler_role" {
  name = "stock-agent-scheduler-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "scheduler.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "invoke_lambda_policy" {
  role = aws_iam_role.scheduler_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["lambda:InvokeFunction"],
      Resource = var.lambda_arn
    }]
  })
}
