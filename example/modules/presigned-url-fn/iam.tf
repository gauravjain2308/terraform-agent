# Module: presigned-url-fn
# IAM — inline policies and resource-based policies

# Read/write S3 objects
data "aws_iam_policy_document" "inline_presigned_url_fn_upload_bucket" {
  statement {
    sid    = "AllowUploadBucket"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket"
    ]
    resources = ["arn:aws:s3:::s3-presigned-url-upload-${var.environment}-upload-bucket/*"]
  }
}

resource "aws_iam_role_policy" "inline_presigned_url_fn_upload_bucket" {
  name   = "${var.project_name}-${var.environment}-presigned-url-fn-upload-bucket"
  role   = var.lambda_execution_name
  policy = data.aws_iam_policy_document.inline_presigned_url_fn_upload_bucket.json
}

resource "aws_lambda_permission" "allow_invoke" {
  count = var.api_gateway_arn != "" ? 1 : 0

  statement_id  = "AllowInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_gateway_arn}/*"
}

