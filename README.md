# IPSI Mastercard BINs updater

Needs to be deployed in same region that BINs DynamoDB table exists in.

## Stack parameters

-   `BinsTableName`: DynamoDB table name.
-   `MastercardSecretName`: Secrets Manager entry name.
-   `MastercardApiUrl`: Allows switching between production and sandbox environments.

## Lambda environment variables

_In case of CloudFormation deployment all environment variables are provided from stack parameters._

-   `BINS_TABLE_NAME`: DynamoDB table name.
-   `SECRET_NAME`: AWS Secrets Manager ID where credentials are stored.
-   `API_URL`: Target API base URL.

## Required resources

-   DynamoDB table for BINs must exist.
-   Secrets Manager entry with following structure:
    ```json
    {
        "password": "<from Mastercard developer portal - keystore password>",
        "consumerKey": "<from Mastercard developer portal>",
        "keyStore": ""
    }
    ```
