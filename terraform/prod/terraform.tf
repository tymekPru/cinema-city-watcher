terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.00"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8.0"
    }
  }

  backend "s3" {
    bucket = "cc-watcher-tfstate-bucket"
    key    = "cc-watcher/terraform.tfstate"
    region = "eu-central-1"

    use_lockfile = true
  }

  required_version = ">= 1.2"
}
