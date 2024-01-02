import base64
import boto3
import datetime
import json
import logging
import mappings
import os
import oauth1.authenticationutils as authenticationutils
import oauth1.oauth as oauth
import requests

KEY_STORE_PATH = "/tmp/ipsi.mastercard.keystore.p12"

# environment setup
table_name = os.environ["BINS_TABLE_NAME"]
secret_name = os.environ["SECRET_NAME"]
api_url = os.environ["API_URL"]
log_level = os.environ.get("LOG_LEVEL", "INFO")

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(log_level)

# fixed resources for lifetime of entire runtime environment
secrets_manager = boto3.client("secretsmanager")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(table_name)

logger.debug(f"Loading credentials from {secret_name}…")
secret = secrets_manager.get_secret_value(SecretId=secret_name)

auth = json.loads(secret["SecretString"])

logger.debug(f"Saving key store as {KEY_STORE_PATH}")
with open(KEY_STORE_PATH, "wb") as file:
    file.write(base64.standard_b64decode(auth["keyStore"]))

signing_key = authenticationutils.load_signing_key(KEY_STORE_PATH, auth["password"])


def fetch_bins():
    page = 1

    while True:
        logger.info(f"Requesting BINs page {page}…")
        url = f"{api_url}bin-resources/bin-ranges?page={page}&size=500"
        logger.debug(f"URL: {url}")
        auth_header = oauth.OAuth.get_authorization_header(url, "POST", None, auth["consumerKey"], signing_key)
        response = requests.post(
            url,
            headers={
                "Authorization": auth_header
            }
        )
        response.raise_for_status()

        payload = json.loads(response.content)
        total = payload["totalItems"]

        logger.debug(f" <- {page * 500} / {total}")
        for entry in payload["items"]:
            yield entry

        if payload["totalPages"] == page:
            break

        page = page + 1

    logger.info(f" =  BINs downloaded")


def build_bins_range(entry):
    start_bin = int(str(entry["lowAccountRange"])[:8])
    end_bin = int(str(entry["highAccountRange"])[:8])
    logger.debug(f"BINs range: {start_bin} … {end_bin}")

    return [str(current_bin) for current_bin in range(start_bin, end_bin + 1)]


# TODO: separate dependencies into Lambda layer (ask?)
def handler(event, context=None):
    # this will differ by seconds but will save us re-calculation for every record
    update_time = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # TODO: handle same BIN entries in response?
    # TODO: handle merging with existing record if other provider also have same bin
    with table.batch_writer() as batch:
        for entry in fetch_bins():
            for current_bin in build_bins_range(entry):
                logger.debug(f" -> Saving BIN {current_bin}")
                batch.put_item(
                    Item={
                        "bin": current_bin,
                        "cardBrand": mappings.acceptance_brand_to_card_brand(entry["acceptanceBrand"]),
                        "cardType": entry["fundingSource"],
                        "cardSubtype": entry["consumerType"],
                        "country": entry["country"]["name"],
                        "issuedOrganization": entry["customerName"],
                        "lastUpdated": update_time,
                        "submittedForUpdate": update_time,
                        "updateStatus": "COMPLETE",
                    }
                )
