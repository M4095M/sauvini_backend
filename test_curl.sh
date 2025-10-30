#!/bin/bash

# Quick CORS and API Testing Script
# Usage: ./test_curl.sh [local|production]

ENV=${1:-local}

if [ "$ENV" = "production" ]; then
    BACKEND_URL="https://sauvini-backend.onrender.com"
    FRONTEND_URL="https://sauvini-frontend.onrender.com"
else
    BACKEND_URL="http://localhost:8000"
    FRONTEND_URL="http://localhost:3000"
fi

API_ENDPOINT="${BACKEND_URL}/api/v1/auth/student/send-verification-email"

echo "=================================="
echo "Testing CORS Configuration"
echo "Environment: $ENV"
echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo "=================================="
echo ""

echo "1. Testing CORS Preflight (OPTIONS request)"
echo "--------------------------------------------"
curl -X OPTIONS "$API_ENDPOINT" \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v 2>&1 | grep -E "(< HTTP|< Access-Control)"
echo ""

echo "2. Testing POST Request with CORS"
echo "--------------------------------------------"
curl -X POST "$API_ENDPOINT" \
  -H "Origin: $FRONTEND_URL" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"email":"test@example.com","user_type":"student"}' \
  -v 2>&1 | grep -E "(< HTTP|< Access-Control|{)"
echo ""

echo "=================================="
echo "Test Complete"
echo "=================================="
echo ""
echo "Look for these in the output:"
echo "  ✅ Access-Control-Allow-Origin header"
echo "  ✅ HTTP/1.1 200 status (or appropriate error)"
echo "  ✅ JSON response body"
echo ""

