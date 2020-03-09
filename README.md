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
[`flask`](https://palletsprojects.com/p/flask/),
[`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
and [`click`](https://click.palletsprojects.com/). (`click` is only
needed for the command line utility for API key management). These
can be installed through the [Python Package Index](https://pypi.org)
by running the command:
```
pip install flask boto3 click
```

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
`sURLy` with a custom domain name. 

**TODO** _Add more detailed instructions_

Add something like the following to your `production` stage in the
`zappa_settings.json`:
```
{
  'domain': 'app.example.com'
  'certificate_arn': 'arn:aws:acm:<my arn>'
  'route53_enabled': false
}
```

## Short URL management API

**TODO** Create, examine and delete shortcodes... read the code for
the time being!

## API key management

**TODO** How to use the `surly_api_key.py` tool.



