import aws_cdk as core
import aws_cdk.assertions as assertions

from aws.availability_aws_stack import AvailabilityAwsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in availability_aws/availability_aws_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AvailabilityAwsStack(app, "availability-aws")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
