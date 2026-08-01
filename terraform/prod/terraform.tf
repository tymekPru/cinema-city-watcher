terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.00"
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