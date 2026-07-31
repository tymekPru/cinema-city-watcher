terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.92"
    }
  }

  backend "s3" {
    bucket = "cc-watcher-tfstate-bucket"
    key    = "my_lambda/terraform.tfstate"
    region = "eu-central-1"
  }

  required_version = ">= 1.2"
}