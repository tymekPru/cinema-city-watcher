#!/bin/bash
find . -name "*.zip" -type f -delete
cd src && zip -r ../build/lambda.zip .