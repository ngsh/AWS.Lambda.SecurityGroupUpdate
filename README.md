# AWS.Lambda.SecurityGroupUpdate

# Doc.AWS.Lambda.SecurityGroupUpdate.Readme

Created: Jan 12, 2021 2:35 PM
Language: Python
Tags: Cloud, Ops, s.wu

## Objective

1. Periodically update security group inbound rules to allow connections coming from below four AWS service endpoints:
    - Amazon API Gateway - [apigateway.cn-north-1.amazonaws.com.cn](http://apigateway.cn-north-1.amazonaws.com.cn/)
    - API Gateway Dataplane - [execute-api.cn-north-1.amazonaws.com.cn](http://execute-api.cn-north-1.amazonaws.com.cn/)
    - API Gateway V2 - [apigateway.cn-north-1.amazonaws.com.cn](http://apigateway.cn-north-1.amazonaws.com.cn/) (same as above)
    - API Gateway Dataplane V2 - [execute-api.cn-north-1.amazonaws.com.cn](http://execute-api.cn-north-1.amazonaws.com.cn/) (same as above)

## Motivation

Since API Gateway proxies API calls directly to backend servers here, the security group of backend servers should have updated entries to explicitly allow inbound connections coming from API Gateway's resolved IP addresses.

## Solution

1. Create a Lambda function (Python) to update security group rules. Procedures of the function:
    1. Data retrieving and data object constructing:
        - Get the existing inbound entries of target security group (using `boto3` api) that are managed by this Lambda function$^1$.
        - Get the current IP resolutions of a list of target hostnames (above 4 endpoints)
    2. Compare the differences of existing entries and up-to-date entries and create a list of entries for deletion and a list of entries for addition$^2$.
    3. Update security group entries accordingly.
2. Execute the Lambda function periodically by creating a rule on CloudWatch.

## Configuration

- `VAR_SGID` accepts a string denoting security group id.
- `VAR_HOSTNAMES` accepts a list of strings of security group entry in the form: `'url:port[:port]'`.

    e.g. `'example.com:443:80'`

## Notes

1. The Lambda function uses the security group rules' comment field to track the rules under management.
2. The size of resolved IP entries of this task is quite small, it may be more convenient to just delete all existing entries and append the new ones. The solution of this task provides a general way to target similar request with different size.

## References

1. AWS Beijing Region Endpoints [https://docs.amazonaws.cn/en_us/aws/latest/userguide/endpoints-Beijing.html](https://docs.amazonaws.cn/en_us/aws/latest/userguide/endpoints-Beijing.html)
2. AWS SDK for Python (Boto3) [https://aws.amazon.com/sdk-for-python/](https://aws.amazon.com/sdk-for-python/)
3. AWS security group rules [https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html#SecurityGroupRules](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html#SecurityGroupRules)

## Appendix

- Data structure of concern:

    ```python
    {
    	PortNumber0: {
    		hostname0: [
    			"ipaddress0",
    			"ipaddress1"
    		],
    		hostname1: [
    			"ipaddress0",
    			"ipaddress1",
    			"ipaddress2"
    		],
    	},
    	PortNumber1: {
    		hostname3: [
    			"ipaddress0",
    			"ipaddress1"
    		]
    	}
    }
    ```

- Sample JSON response of `describe_seurity_groups` method call of `boto3`:

    ```json
    {
        "SecurityGroups": [
            {
                "Description": "Managed by Terraform",
                "GroupName": "terraform-20201229110623482400000001",
                "IpPermissions": [
                    {
                        "FromPort": 80,
                        "IpProtocol": "tcp",
                        "IpRanges": [
                            {
                                "CidrIp": "8.8.8.8/32",
                                "Description": "nameserver:"
                            },
                            {
                                "CidrIp": "8.8.4.4/32",
                                "Description": "name:"
                            }
                        ],
                        "Ipv6Ranges": [],
                        "PrefixListIds": [],
                        "ToPort": 80,
                        "UserIdGroupPairs": []
                    },
                    {
                        "FromPort": 443,
                        "IpProtocol": "tcp",
                        "IpRanges": [
                            {
                                "CidrIp": "54.222.252.160/32",
                                "Description": "apigateway.cn-north-1.amazonaws.com.cn:DO NOT MODIFY"
                            },
                            {
                                "CidrIp": "54.223.28.35/32",
                                "Description": "apigateway.cn-north-1.amazonaws.com.cn:DO NOT MODIFY"
                            }
                        ],
                        "Ipv6Ranges": [],
                        "PrefixListIds": [],
                        "ToPort": 443,
                        "UserIdGroupPairs": []
                    }
                ],
                "OwnerId": "xxxxxxxxxxxx",
                "GroupId": "sg-xxxxxxxxxxxxxxxxx",
                "IpPermissionsEgress": [
                    {
                        "FromPort": 8,
                        "IpProtocol": "icmp",
                        "IpRanges": [
                            {
                                "CidrIp": "0.0.0.0/0"
                            }
                        ],
                        "Ipv6Ranges": [],
                        "PrefixListIds": [],
                        "ToPort": 0,
                        "UserIdGroupPairs": []
                    }
                ],
                "Tags": [
                    {
                        "Key": "Name",
                        "Value": "SWLAB-SG-LAMBDA"
                    },
                    {
                        "Key": "Project",
                        "Value": "SWLAB"
                    }
                ],
                "VpcId": "vpc-xxxxxxxxxxxxxxxxx"
            }
        ],
        "ResponseMetadata": {
            "RequestId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "HTTPStatusCode": 200,
            "HTTPHeaders": {
                "x-amzn-requestid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "cache-control": "no-cache, no-store",
                "strict-transport-security": "max-age=31536000; includeSubDomains",
                "content-type": "text/xml;charset=UTF-8",
                "content-length": "2998",
                "vary": "accept-encoding",
                "date": "Thu,
                31 Dec 2020 10: 04: 36 GMT", "server": "AmazonEC2"
            },
            "RetryAttempts": 0
        }
    }
    ```
