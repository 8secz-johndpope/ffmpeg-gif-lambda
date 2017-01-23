import logging
import boto3
import os
import subprocess
import errno
import uuid
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
bin_dir = os.path.join(os.getcwd(), 'bin')


MAX_FILE_SIZE = 1024 * 1024 * 10
OUT_FILE = "/tmp/out.gif"


def make_response(status_code, headers=None, body=None):
    return {
        "statusCode": status_code,
        "headers": headers if headers else {},
        "body": body if body else "",
    }


def parse_query_string_args(args):
    valid_args = ['key', 'bucket']

    if set(valid_args) != set(args.keys()):
        raise ValueError("Missing or unexpected argument. Required args: {}".format(valid_args))

    for k, v in args.iteritems():
        if not v or str(v) == '':
            raise ValueError("Argument '{}' is malformed ('{}').".format(k, v))

    return {
        'key': str(args.get('key')),
        'bucket': str(args.get('bucket')),
    }


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def lambda_handler(event, context):
    logger.info('got event: {}'.format(event))

    try:
        args = parse_query_string_args(event.get('queryStringParameters'))
    except ValueError as e:
        return make_response(400, body="Invalid Request: {}".format(e.message))

    bucket = args['bucket']
    key = args['key']

    logger.info("bucket: {}, key: {}".format(bucket, key))
    path = '/tmp/{}'.format(uuid.uuid4())
    mkdir_p(path)
    in_file = "{}/{}".format(path, key)

    logger.info("checking file size of {}/{}".format(bucket, key))
    head = s3_client.head_object(Bucket=bucket, Key=key)
    if head['ContentLength'] > MAX_FILE_SIZE:
        return make_response(400, body="File size to large. File size: {}, Max: {} bytes.".format(head['ContentLength'],
                                                                                                  MAX_FILE_SIZE))
    logger.info("file size: {}".format(head['ContentLength']))

    logger.info("downloading {}/{} to {}".format(bucket, key, in_file))
    s3_client.download_file(bucket, key, in_file)

    command = 'PATH=$PATH:{} INFILE={} OUTFILE={} /var/task/bin/giffmpeg.sh'.format(bin_dir, in_file, OUT_FILE)
    logger.info(command)
    ret = subprocess.check_output(command, shell=True)
    logger.info(ret)

    s3_client.upload_file(OUT_FILE, bucket, "{}.gif".format(key))

    return make_response(200, body="https://s3-us-west-2.amazonaws.com/{}/{}.gif".format(bucket, key))
