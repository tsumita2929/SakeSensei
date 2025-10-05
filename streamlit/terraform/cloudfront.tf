# ============================================================================
# CloudFront Distribution
# ============================================================================

# Random secret for custom header (to restrict ALB access to CloudFront only)
resource "random_password" "cloudfront_secret" {
  length  = 32
  special = false
}

# CloudFront Origin Request Policy for WebSocket support
resource "aws_cloudfront_origin_request_policy" "websocket_policy" {
  name    = "${var.project_name}-websocket-policy-${var.environment}"
  comment = "Policy for WebSocket support with all headers forwarded"

  cookies_config {
    cookie_behavior = "all"
  }

  headers_config {
    header_behavior = "allViewer"
  }

  query_strings_config {
    query_string_behavior = "all"
  }
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Sake Sensei Streamlit App Distribution"
  default_root_object = ""
  price_class         = "PriceClass_All"

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    # Custom header to validate requests from CloudFront
    custom_header {
      name  = "X-Custom-Header"
      value = random_password.cloudfront_secret.result
    }
  }

  default_cache_behavior {
    allowed_methods          = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods           = ["GET", "HEAD"]
    target_origin_id         = "alb-origin"
    viewer_protocol_policy   = "redirect-to-https"
    compress                 = true
    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # AWS Managed-CachingDisabled
    origin_request_policy_id = aws_cloudfront_origin_request_policy.websocket_policy.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-distribution-${var.environment}"
  }
}

# Store the custom header secret in SSM Parameter Store for reference
resource "aws_ssm_parameter" "cloudfront_secret" {
  name        = "/${var.project_name}/${var.environment}/cloudfront-custom-header"
  description = "Custom header secret for CloudFront to ALB communication"
  type        = "SecureString"
  value       = random_password.cloudfront_secret.result

  tags = {
    Name = "${var.project_name}-cloudfront-secret-${var.environment}"
  }
}
