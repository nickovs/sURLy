# sURLy: A simple URL shortener

`sURLy` is designed to allow an organisation to deploy a private,
access-controlled URL shortener service.

`sURLy` is built using the
[`flask`](https://palletsprojects.com/p/flask/) WSGI framework and uses
[AWS](https://aws.amazon.com) [DynamoDB](https://aws.amazon.com/dynamodb/)
to store the destination URLs as well as the API key access control
information. Use of a WSGI framwork allows it to be deployed in
[wide variety](https://wsgi.readthedocs.io/en/latest/servers.html) of
production environments as well as allowing for easy local
testing. Since it uses DynamoDB for the database it naturally lends
itself to deployment in AWS and it was designed with the intention of
being deployed in AWS [Lambda](https://aws.amazon.com/lambda/) through
use of the [`zappa`](https://github.com/Miserlou/Zappa) "serverless"
deployment tool (although it can easily be deployed elsewhere).

## Depenencies

The only direct dependencies for `sURLy` are
[`flask`](https://palletsprojects.com/p/flask/) and
[`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html).
These can be installed through the [Python Package Index](https://pypi.org)
by running the command: ``` pip install flask boto3 ```

For deployment into the AWS Lambda the easy way you will also want to install
`zappa`:
```
pip install zappa
```

## Deployment in AWS Lambda

Assuming that you already have AWS credentials installed on your
machine, and that you have installed `flask`, `boto3` and `zappa`, you
can deploy a development version of `sURLy` by simply typing:
```
zappa deploy
```

This will configure all of the necessary settings in AWS, upload the
code, start the Lambda service and ultimately print the URL of the API
gateway endpoint where the service runs.

For production services a _little_ more work is required to improve both
security and usability. The default development deployment will grant
your Lambda service wide-reaching access rights; you will want to
restrict it to nothing more than accessing the DynamoDB
database. Also, by default the URL of the API endpoint is long and
complex, so the resulting shorted URLs end up being long!

**TODO** _Add instructions on securing access rights._ See [zappa docs](https://github.com/Miserlou/Zappa#custom-aws-iam-roles-and-policies-for-deployment)
for details.

The problem of long "shortened" URLs is easily fixed by deploying
`sURLy` with a custom domain name.  There are three parts to doing
this:

 1) Configure a certificate and key for SSL/TLS for the custom domain.
 1) Configure `zappa` to use the custom domain.
 1) Point the custom domain name to the API gateway endpoint for the
 service.

The ease of performing these three steps depends very much on if you
make use of AWS's Route 53 DNS service. Amazon provides a number of
tools to smooth the deployment significantly if you are using Amazon's
own DNS but the is still relatively straightforward to do this without
Route 53. You can also choose to use your own keys and certificates or
you can use AWS Certificate Manager (ACM) to generate its own keys and
certificates.

### Deploying with `zappa`, Route 53 and ACM certificates.

Go to AWS ACM and request a certificate for the desired domain, using
DNS domain control authentication. This returns the ARN for the
certifciate.

Setup `zappa_settings.json` with something like the following:

```
{
  'domain': 'app.example.com'
  'certificate_arn': 'arn:aws:acm:<my arn>'
  'route53_enabled': true
}
```

Run:

```
zappa certify
zappa deploy
```

### Deploying with `zappa` and ACM cetificates but without Route 53

Go to AWS ACM and request a certificate for the desired domain, using
whichever sort of verification methos DNS domain control authentication. This returns the ARN for the
certifciate.

Setup `zappa_settings.json` with something like the following:

```
{
  'domain': 'app.example.com'
  'certificate_arn': 'arn:aws:acm:<my arn>'
  'route53_enabled': false
}
```

Run:

```
zappa certify
zappa deploy
```

Record the address of the API endpoint.

Create a CNAME record to point the desired domain name to the API
endpoint.

You will need to fix this record if you ever undeploy and redeploy the
service (but not if you use `zappa update`).


### Deploying with `zappa` without ACM or Route 53

Create a key pair. Get a certificate for the public key at the desired
endpoint name. Upload the key, cert and cert chain to ACM. This yields
an ARN for your non-ACM certifcate.


Add something like the following to your `production` stage in the
`zappa_settings.json`:

```
{
  'domain': 'app.example.com'
  'certificate_arn': 'arn:aws:acm:<my arn>'
  'route53_enabled': false
}
```

Record the address of the API endpoint.

Create a CNAME record to point the desired domain name to the API
endpoint.

You will need to fix this record if you ever undeploy and redeploy the
service (but not if you use `zappa update`).



## Short URL management API

* Create a shortcode: `POST /api/v1/shortcode`.
  * Parameters (sent using formal web form (`application/x-www-form-urlencoded`) encoding:
    * `account_id`: (required) string to identify the application or user
  creating the shortcode.
    * `api_key`: (required) 'secret' string to authenticate the requesting account.
    * `target`: (required) URL for the desitnation of the shortcode link.
    * `prefix`: (optional) if present the short code will start with this
string.
    * `length`: (optional) number of random characters in the
    shortcode
  * Return (as a  JSON object)



* Check details of the shortcode: `GET /api/v1/shortcode/<code>`.
  * Parameters encoded as an HTTP quesry string:
    * `account_id`: (required) string to identify the application or user
  creating the shortcode.
    * `api_key`: (required) 'secret' string to authenticate the requesting account.

* Delete a shortcode: `DELETE /api/v1/shortcode/<code>`.
  * Parameters encoded as an HTTP quesry string:
    * `account_id`: (required) string to identify the application or user
  creating the shortcode.
    * `api_key`: (required) 'secret' string to authenticate the requesting account.


**TODO** Create, examine and delete shortcodes... read the code for
the time being!

## API key management

**TODO** How to use the `api_key_tool.py` tool.

## Running locally for testing

If you want to test the code by running it locally you can run `flask`
directly:

```
FLASK_DEBUG=1 FLASK_APP=surly.py flask run
```
