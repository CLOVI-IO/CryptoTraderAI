#!/bin/bash
echo 'http {
    types_hash_max_size 2048;
    types_hash_bucket_size 128;
}' >> /etc/nginx/conf.d/custom.conf
service nginx restart