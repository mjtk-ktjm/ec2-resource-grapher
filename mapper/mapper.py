import boto3
from graphviz import Digraph
import re
from pprint import pprint as pp
import sys

resources_found = list()
interesting_fields = {  'i' : [
                                'BlockDeviceMappings',
                                'ImageId',
                                'InstanceId',
                                'SecurityGroups',
                                ],
                        'vol' : [
                                'snap'
                                ],
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


def asset_type(arn):
    short_type, arn_int = arn.split('-')
    if short_type == 'i':
        return 'Instance'
    elif short_type == 'vol':
        return 'Volume'
    elif short_type == 'snap':
        return 'Snapshot' 
    elif short_type == 'ami':
        return 'Image' 
    elif short_type == 'sg':
        return 'SecurityGroup'


def flatten_tags(tags=None):
    if tags is None or len(tags) == 0:
        return ''
    tag_list = [list(x) for x in [y.values() for y in tags]]
    formatted_tags = [str(val[0])+'='+str(val[1]) for val in tag_list]
    return '\n'.join(formatted_tags)


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
        self.payload = None
        self.ref_time = None
        self.asset_id = None


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

        # quick_payload = payload['Reservations'][0]['Instances'][0]
        # quick_payload['asset_is'] = quick_payload['InstanceId']
        self.payload = payload['Reservations'][0]['Instances'][0]
        self.asset_id = payload['Reservations'][0]['Instances'][0]['InstanceId']
        self.ref_time = payload['Reservations'][0]['Instances'][0]['LaunchTime']
        # return quick_payload


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

        # return_payload = payload['Volumes'][0]
        # return_payload['asset_is'] = return_payload['VolumeId']
        # return return_payload
        self.payload = payload['Volumes'][0]
        self.asset_id = payload['Volumes'][0]['InstanceId']


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

        self.payload = payload['Snapshots'][0]
        self.asset_id =  payload['Snapshots'][0]['SnapshotId']
        # return_payload = payload['Snapshots'][0]
        # return_payload['asset_is'] = return_payload['SnapshotId'] 
        # return return_payload


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

        self.payload =  payload['Images'][0]
        self.asset_id =  payload['Images'][0]['ImageId']
        # return_payload = payload['Images'][0]
        # return_payload['asset_is'] = return_payload['ImageId']
        # return return_payload


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

        self.payload = payload['SecurityGroups'][0]
        self.asset_id = payload['SecurityGroups'][0]['GroupId']
        # return_payload = payload['SecurityGroups'][0]
        # return_payload['asset_is'] = return_payload['GroupId']
        # return return_payload


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
    # arns.append('vol-0e566a70d756391eb')
    # arns.append('vol-0151f28dcf5e7ba9d')
    # arns.append('ami-7c8a776a')
    # arns.append('sg-525be129')

    assets = []

    for arn in arns:
        print('\n\nFetching {}:'.format(arn))
        asset_payload = get_arn_type_func(arn)
        # asset_payload.fetch_asset()
        # pp(asset_payload.asset_id)
        
        assets.append(asset_payload.fetch_asset())

    # pp(assets)
    
    sys.exit()

    for a in assets:
        if 'Tags' in a.keys():
            print()
            print(a['asset_is'])
            print(flatten_tags(a['Tags']))


    r = Instance(arn)
    r.print_asset_arn()
    print(r.arn_type())
    r.fetch_asset()

