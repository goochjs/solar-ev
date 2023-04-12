import json
import os

import requests


def lambda_handler(event, context):
    # Get Solcast API Key and location from environment variables
    solcast_api_key = os.environ["SOLCAST_API_KEY"]
    location = json.loads(os.environ["LOCATION"])

    # Query Solcast API for solar radiation data
    url = f'https://api.solcast.com.au/radiation/forecasts?longitude={location["longitude"]}&latitude={location["latitude"]}&api_key={solcast_api_key}'
    response = requests.get(url)

    if response.status_code == 200:
        # Extract the estimated global_horizontal_irradiance value from the Solcast API response
        breakpoint()
        solcast_data = json.loads(response.content.decode("utf-8"))
        ghi = solcast_data["forecasts"][0]["ghi"]

        # Calculate the desired battery charge level
        # Example: Set battery charge level to 80% if solar radiation is greater than 500 W/m2, otherwise set to 30%
        if ghi > 500:
            battery_charge_level = 80
        else:
            battery_charge_level = 30

        # Set the battery charge level using the GivEnergy API
        # Note: This example assumes that you have already set up the necessary credentials and API endpoints for GivEnergy
        givenergy_api_key = os.environ["GIVENERGY_API_KEY"]
        url = "https://api.givenergy.cloud/v1.0/device/control"
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {givenergy_api_key}",
        }
        data = {"battery_charge_level": battery_charge_level}
        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return {
                "statusCode": 200,
                "body": f"Successfully set battery charge level to {battery_charge_level}%",
            }
        else:
            return {"statusCode": response.status_code, "body": response.text}
    else:
        return {"statusCode": response.status_code, "body": response.text}


def main():
    lambda_handler(None, None)


if __name__ == "__main__":
    main()
