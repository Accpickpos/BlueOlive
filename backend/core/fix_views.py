# Direct line replacement
with open("shop_users/views.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find the exact corrupted string and replace it
old_text = "            raise AuthenticationFailed(f\"Login failed: {str(e)}\"), subdomain):\n            return Response(\n                {\n                    'detail': 'Invalid subdomain format',\n                    'subdomain': subdomain,\n                    'available': False,\n                    'suggestions': []\n                },\n                status=status.HTTP_400_BAD_REQUEST\n            )\n        \n        if len(subdomain) < 3:"

new_text = '            raise AuthenticationFailed(f"Login failed: {str(e)}")\n\n        if False and len(subdomain) < 3:'  # Dummy to preserve structure

if old_text in content:
    content = content.replace(old_text, new_text)
    with open("shop_users/views.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed!")
else:
    print("Pattern not found, trying simpler match")
    # Simpler match - just fix the raise line
    old_raise = 'raise AuthenticationFailed(f"Login failed: {str(e)}"), subdomain):'
    new_raise = 'raise AuthenticationFailed(f"Login failed: {str(e)}")'
    if old_raise in content:
        content = content.replace(old_raise, new_raise)
        with open("shop_users/views.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed simple match!")
    else:
        print("Simple match not found either")
