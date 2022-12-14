
from aws_cdk import (
    aws_dynamodb as ddb,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_kinesis as kinesis,
    aws_ssm as ssm,
    CfnOutput,
    Stack,
)
from constructs import Construct


class InfraStack(Stack):

  vpc: ec2.Vpc
  fargate: ecs.Cluster
  cdc_stream: kinesis.Stream
  availability_eventstore: ddb.Table
  availability_consumer_tbl: ddb.Table
  availability_tbl: ddb.Table

  def __init__(self, scope: Construct, construct_id: str, *args, **kwargs):
    super().__init__(scope, construct_id, *args, **kwargs)

    self.vpc = ec2.Vpc(self, 'vpc', max_azs=2)
    self.fargate = ecs.Cluster(self, 'fargate')

    self.cdc_stream = kinesis.Stream(self, 'cdc-stream', stream_name='availability-cdc', shard_count=2)
    self.availability_eventstore = ddb.Table(self, 'availability-eventstore',
      table_name='availability-event-store',
      partition_key=ddb.Attribute(name='user_id', type=ddb.AttributeType.STRING),
      sort_key=ddb.Attribute(name='version', type=ddb.AttributeType.NUMBER),
      read_capacity=2,
      write_capacity=2,
      stream=ddb.StreamViewType.NEW_IMAGE,
      kinesis_stream=self.cdc_stream
    )
    self.availability_consumer_tbl = ddb.Table(self, 'availability-consumer-tbl',
      table_name='availability-consumer',
      partition_key=ddb.Attribute(name='shard', type=ddb.AttributeType.STRING),
      read_capacity=2,
      write_capacity=2
    )
    self.availability_tbl = ddb.Table(self, "availability-read-model",
      table_name='availability-read-model',
      partition_key=ddb.Attribute(name='user_id', type=ddb.AttributeType.STRING),
      sort_key=ddb.Attribute(name='time_slot', type=ddb.AttributeType.STRING),
      read_capacity=2,
      write_capacity=2
    )

    CfnOutput(self, 'event-store-tbl-name', value=self.availability_eventstore.table_name)
    CfnOutput(self, 'cdc-stream-name', value=self.cdc_stream.stream_name)
    CfnOutput(self, 'availability-consumer-tbl-name', value=self.availability_consumer_tbl.table_name)
    CfnOutput(self, 'availability-readmodel-tbl-name', value=self.availability_tbl.table_name)
