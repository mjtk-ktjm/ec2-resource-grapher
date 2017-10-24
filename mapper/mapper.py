import boto3
from graphviz import Digraph
import re
from pprint import pprint as pp
import sys

resources_found = list()
interesting_fields = {  'i' : ['BlockDeviceMappings','ImageId','InstanceId','SecurityGroups'],
                        'vol' : ['snap'],
                        'ami' : [],
                        'snap' : [],
                        'sg' : [],
                    }

ec2 = boto3.client('ec2')

def get_arn_type_func(arn):
    short_type, arn_int = arn.split('-')
    if short_type == 'i':
        return Instance(arn)
    elif short_type == 'vol':
        return Volume(arn)
    elif short_type == 'snap':
        return Snapshot(arn) 
    elif short_type == 'ami':
        return Image(arn) 
    elif short_type == 'sg':
        return SecurityGroup(arn)

class Asset:
    """
    Base Class for amazon assets.
    """

    def __init__(self, arn):

        if arn in resources_found:
            print("Already found ", arn)
            return None
        else:
            resources_found.append(arn)

        self.arn = arn
        self.children = None
        self.tag_str = None

    def print_asset_arn(self):
        print(self.arn + ' : yay!')


class Instance(Asset):
    """

    """
    def fetch_asset(self):
        try:
            payload = ec2.describe_instances(InstanceIds=[self.arn])
        except:
            print('Instance does not exist.')
            return None
        
        payload.keys()
        if 'Reservations' not in payload.keys() or len(payload['Reservations'])==0:
            print('Zero reservations.')
            return None

        if len(payload['Reservations'])>1:
            print('More than 1 reservation here!')

        if len(payload['Reservations'][0]['Instances'])>1:
            print('More than 1 instance here!')

        pp(payload['Reservations'][0]['Instances'][0])
        return payload['Reservations'][0]['Instances'][0]


class Volume(Asset):
    """

    """
    def fetch_asset(self):
        try:
            payload = ec2.describe_volumes(VolumeIds=[self.arn])
        except:
            print('Volume does not exist.')
            return None

        if 'Volumes' not in payload.keys() or len(payload['Volumes'])==0:
            print('Zero reservations.')
            return None

        if len(payload['Volumes'])>1:
            print('More than 1 volume here!')

        pp(payload['Volumes'][0])
        return payload['Volumes'][0]


class Snapshot(Asset):
    """

    """
    def fetch_asset(self):
        try:
            payload = ec2.describe_snapshots(SnapshotIds=[self.arn])
        except:
            print('Snapshot does not exist.')
            return None

        if 'Snapshots' not in payload.keys() or len(payload['Snapshots'])==0:
            print('Zero snapshots.')
            return None

        if len(payload['Snapshots'])>1:
            print('More than 1 snapshot here!')

        pp(payload['Snapshots'][0])
        return payload['Snapshots'][0]


class Image(Asset):
    """

    """
    def fetch_asset(self):
        try:
            payload = ec2.describe_images(ImageIds=[self.arn])
        except:
            print('Image does not exist.')
            return None

        if 'Images' not in payload.keys() or len(payload['Images'])==0:
            print('Zero images.')
            return None

        if len(payload['Images'])>1:
            print('More than 1 image here!')

        pp(payload['Images'][0])
        return payload['Images'][0]


class SecurityGroup(Asset):
    """

    """
    def fetch_asset(self):
        try:
            payload = ec2.describe_security_groups(GroupIds=[self.arn])
        except:
            print('Security Group does not exist.')
            return None

        if 'SecurityGroups' not in payload.keys() or len(payload['SecurityGroups'])==0:
            print('Zero Groups.')
            return None

        if len(payload['SecurityGroups'])>1:
            print('More than 1 group here!')

        pp(payload['SecurityGroups'][0])
        return payload['SecurityGroups'][0]


if __name__ == '__main__':
    """

    """


    arns = list()

    # arns.append('vol-596aeefe')# volume eg
    # arns.append('snap-25dd2ac1')# volume eg
    # arns.append('i-836b9d9b')# instance eg
    # arns.append('ami-6869aa05')
    # arns.append('i-836b9d9b')# instance eg

    arns.append('i-0b2efb42fb389c3fb')
    arns.append('vol-0e566a70d756391eb')
    arns.append('vol-0151f28dcf5e7ba9d')
    arns.append('ami-7c8a776a')
    arns.append('sg-525be129')

    for arn in arns:
        print('\n\nFetching {}:'.format(arn))
        z = get_arn_type_func(arn)
        z.fetch_asset()


    print(resources_found)

    sys.exit()

    r = Instance(arn)
    r.print_asset_arn()
    print(r.arn_type())
    r.fetch_asset()

