#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws.infra_stack import InfraStack


app = cdk.App()

env = cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))

infra_stack = InfraStack(app, "availability-infra", env=env, stack_name='availability-infra')

app.synth()
