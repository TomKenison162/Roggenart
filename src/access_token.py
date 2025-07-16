def get_access_token():
    """
    Retrieves an access token from the Toast API using the client credentials grant flow.
    """
    auth_url = f"{API_HOSTNAME}/authentication/v1/authentication/login"
    headers = {
        "Content-Type": "application/json",
        "Toast-Restaurant-External-ID": "aea8d7f1-0daa-447b-aa43-8d71ee6b6402" 
    }
    payload = {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET,
        "userAccessType": "TOAST_MACHINE_CLIENT"
    }

    print(f"Requesting access token from: {auth_url}")

    try:
        response = requests.post(auth_url, headers=headers, json=payload)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)

        token_data = response.json()
        access_token = token_data.get("token", {}).get("accessToken")

        if not access_token:
            print("Error: Access token not found in the response.")
            print("Response:", response.text)
            return None

        print("Successfully retrieved access token!")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the request: {e}")
        if e.response:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
        return None
    except json.JSONDecodeError:
        print("Error: Failed to decode JSON from response.")
        print("Response:", response.text)
        return None