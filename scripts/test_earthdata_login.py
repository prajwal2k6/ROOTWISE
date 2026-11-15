
import earthaccess

print("Connecting to NASA Earthdata...")

auth = earthaccess.login(strategy="interactive")

if auth.authenticated:
    print("SUCCESS: ROOTWISE connected to NASA Earthdata!")
else:
    print("Login failed. Please check your credentials.")
