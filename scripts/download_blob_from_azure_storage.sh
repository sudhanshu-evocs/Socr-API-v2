#!/bin/bash

file_name=$1

download_path="C:\\Workspace\\files\\"
container_name=""
account_name=""
sas_token=""

az storage blob download --account-name $account_name -c $container_name --name "$file_name"  --file "$download_path$file_name" --sas-token $sas_token
