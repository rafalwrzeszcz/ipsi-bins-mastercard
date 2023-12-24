import base64
import boto3
import datetime
import json
import os
import oauth1.authenticationutils as authenticationutils
import oauth1.oauth as oauth
import requests

KEY_STORE_PATH = "/tmp/ipsi.mastercard.keystore.p12"

# environment setup
table_name = os.environ["BINS_TABLE_NAME"]
secret_name = os.environ["SECRET_NAME"]
api_url = os.environ["API_URL"]

# fixed resources for lifetime of entire runtime environment
secrets_manager = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)

print(f"Loading credentials from {secret_name}…")
secret = secrets_manager.get_secret_value(SecretId=secret_name)

auth = json.loads(secret["SecretString"])

print(f"Saving key store as {KEY_STORE_PATH}")
with open(KEY_STORE_PATH, "wb") as file:
    file.write(base64.standard_b64decode(auth["keyStore"]))

signing_key = authenticationutils.load_signing_key(KEY_STORE_PATH, auth["password"])


def fetch_bins():
    page = 1

    while True:
        print(f"Requesting BINs page {page}…")
        url = f"{api_url}bin-ranges?page={page}&size=500"
        auth_header = oauth.OAuth.get_authorization_header(url, "GET", None, auth["consumerKey"], signing_key)
        response = requests.post(
            url,
            headers={
                "Authorization": auth_header
            }
        )
        response.raise_for_status()

        payload = json.loads(response.content)
        total = payload["totalRecords"]

        print(f" <- {page * 500} / {total}")
        for entry in payload["items"]:
            yield entry

        if payload["totalPages"] == page:
            break

        page = page + 1

    print(f" =  BINs downloaded")


def handler(event, context=None):
    # this will differ by seconds but will save us re-calculation for every record
    update_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # TODO: handle same BIN entries in response?
    # TODO: handle merging with existing record if other provider also have same bin
    for entry in fetch_bins():
        current_bin = entry["binNum"]
        print(f" -> Saving BIN {current_bin}")
        # TODO: batch write
        table.put_item(
            Item={
                "bin": current_bin,
                "cardBrand": ["MASTERCARD"],
                "cardType": entry["fundingSource"],
                "cardSubtype": entry["productDescription"],
                "country": entry["country"]["name"],
                "issuedOrganization": entry["customerName"],
                "lastUpdated": update_time,
                "submittedForUpdate": "1990-01-01T00:00:00.000Z",
                "updateStatus": "COMPLETE",
            }
        )


# TODO: this is temporary for test purposes
if __name__ == "__main__":
    handler(None, None)
