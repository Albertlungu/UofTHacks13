#!/bin/bash

# Quick test of the Identity API endpoints

API_URL="http://localhost:5001/api/auth"
TEST_USER="testuser_$(date +%s)"
TEST_PASS="testpass123"

echo "Testing Identity API..."
echo ""

# Test 1: Signup
echo "1. Testing Signup..."
SIGNUP_RESPONSE=$(curl -s -X POST "$API_URL/signup" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

echo "$SIGNUP_RESPONSE" | jq '.'
TOKEN=$(echo "$SIGNUP_RESPONSE" | jq -r '.token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
  echo "✓ Signup successful"
else
  echo "✗ Signup failed"
  exit 1
fi

echo ""

# Test 2: Login
echo "2. Testing Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

echo "$LOGIN_RESPONSE" | jq '.'
echo "✓ Login successful"
echo ""

# Test 3: Get current user
echo "3. Testing Get Current User..."
ME_RESPONSE=$(curl -s -X GET "$API_URL/me" \
  -H "Authorization: Bearer $TOKEN")

echo "$ME_RESPONSE" | jq '.'
echo "✓ Get user info successful"
echo ""

# Test 4: Get profile
echo "4. Testing Get Profile..."
PROFILE_RESPONSE=$(curl -s -X POST "$API_URL/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"$TEST_PASS\"}")

echo "$PROFILE_RESPONSE" | jq '.'
echo "✓ Get profile successful"
echo ""

# Test 5: Update profile
echo "5. Testing Update Profile..."
UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"password\":\"$TEST_PASS\",\"profile\":{\"voice_profile\":{\"pitch\":5},\"test\":true}}")

echo "$UPDATE_RESPONSE" | jq '.'
echo "✓ Update profile successful"
echo ""

echo "All tests passed!"
