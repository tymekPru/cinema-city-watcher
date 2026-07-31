provider "aws" {
  region = "eu-central-1"
}

# Create bucket for tfstate
resource "aws_s3_bucket" "terraform_state" {
  bucket = "cc-watcher-tfstate-bucket"

  # Prevent accidental deletion of this S3 bucket
  lifecycle {
    prevent_destroy = true
  }
}

# Create dynamodb table
resource "aws_dynamodb_table" "cc-watcher-state" {
  name           = "cc-watcher-state"
  hash_key       = "pk"
  read_capacity  = 10
  write_capacity = 5

  attribute {
    name = "pk"
    type = "S"
  }
}

# Create Role
resource "aws_iam_role" "role" {
  name = "CinemaCityWatcherLambda"

  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Effect" : "Allow",
          "Principal" : {
            "Service" : "lambda.amazonaws.com"
          },
          "Action" : "sts:AssumeRole"
        }
      ]
    }
  )
}

# 1. Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_execution_policy" {
  role       = aws_iam_role.role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 2. DynamoDB table access policy
data "aws_iam_policy_document" "dynamodb_policy" {
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem", "dynamodb:GetItem"]
    resources = [aws_dynamodb_table.cc-watcher-state.arn]
  }
}
resource "aws_iam_policy" "dynamodb_policy" {
  name   = "AccessDynamoDbCCWatcherStateTable"
  policy = data.aws_iam_policy_document.dynamodb_policy.json
}
resource "aws_iam_role_policy_attachment" "dynamodb_policy" {
  role       = aws_iam_role.role.name
  policy_arn = aws_iam_policy.dynamodb_policy.arn
}

# 3. SES sending email to me policy
data "aws_iam_policy_document" "ses_policy" {
  statement {
    effect    = "Allow"
    actions   = ["ses:SendEmail"]
    resources = ["arn:aws:ses:eu-central-1:000000000000:identity/alerts@example.com"]
  }
}
resource "aws_iam_policy" "ses_policy" {
  name   = "SendEmailToMeSES"
  policy = data.aws_iam_policy_document.dynamodb_policy.json
}
resource "aws_iam_role_policy_attachment" "ses_policy" {
  role       = aws_iam_role.role.name
  policy_arn = aws_iam_policy.ses_policy.arn
}

# Create Lambda
resource "aws_lambda_function" "py_lambda" {
  filename      = "../build/lambda.zip"
  function_name = "CinemaCityWatcher"
  role          = aws_iam_role.role.arn
  handler       = "lambda_handler.handler"
  runtime       = "python3.12"
  memory_size   = 256
  timeout       = 55

  architectures = ["arm64"]

  environment {
    variables = {
      CAPACITY           = 385
      CINEMA_ID          = 1052
      DDB_TABLE          = cc-watcher-state
      FILM_ID            = "7268s2r"
      FILM_MATCH         = "odys"
      HORIZON_DAYS       = 45
      NOTIFY_BACKEND     = "ses"
      REQUIRED_ATTRS     = "70-mm"
      SES_FROM           = "alerts@example.com"
      SES_TO             = "alerts@example.com"
      STATE_BACKEND      = "dynamodb"
      WATCHER_AWS_REGION = "eu-central-1"
    }
  }
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Create role for scheduler
resource "aws_iam_role" "scheduler_role" {
  name = "CinemaCityWatcherSchedulerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "scheduler.amazonaws.com"
      }

      Action = "sts:AssumeRole"

      Condition = {
        StringEquals = {
          "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          "aws:SourceArn"     = "arn:aws:scheduler:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:schedule-group/default"
        }
      }
    }]
  })
}

# Attatch policy to role 
data "aws_iam_policy_document" "lambda_trigger_policy" {
  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = ["arn:aws:lambda:eu-central-1:000000000000:function:CinemaCityWatcher"]
  }
}
resource "aws_iam_policy" "lambda_trigger_policy" {
  name   = "Amazon-EventBridge-Scheduler-Execution"
  policy = data.aws_iam_policy_document.lambda_trigger_policy.json
}
resource "aws_iam_role_policy_attachment" "lambda_trigger_policy" {
  role       = aws_iam_role.scheduler_role.name
  policy_arn = aws_iam_policy.lambda_trigger_policy.arn
}

# Create EventBridge Scheduler
resource "aws_scheduler_schedule" "scheduler" {
  name       = "CinemaCityWatcherSchedule"
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 minutes)"

  target {
    arn      = aws_lambda_function.py_lambda.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}
