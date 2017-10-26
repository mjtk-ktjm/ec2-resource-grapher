import boto3
from graphviz import Digraph
import re
from pprint import pprint as pp
import sys

resources_found = list()
resource_tree = dict()
direct_descendants = dict()

interesting_fields = {'Instance':['BlockDeviceMappings','ImageId','SecurityGroups'],
                    'Volume':['','',],
                    'Snapshot':['','',],
                    'Image':['','',],
                    'SecurityGroup':['','',],
                    }

fuzzy_fields = {'Instance':{'_id':'InstanceId','_time':'LaunchTime'},
                'Volume':{'_id':'VolumeId','_time':'LaunchDate'},
                'Snapshot':{'_id':'SnapShotId','_time':'LaunchDate'},
                'Image':{'_id':'ImageId','_time':'LaunchDate'},
                'SecurityGroup':{'_id':'GroupId','_time':'LaunchDate'},
                }

ec2 = boto3.client('ec2')


def get_arn_type(arn):
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


def fetch_asset_obj(arn):
    arn_type = get_arn_type(arn)
    if arn_type == 'Instance':
        return Instance(arn)
    elif arn_type == 'Volume':
        return Volume(arn)
    elif arn_type == 'Snapshot':
        return Snapshot(arn) 
    elif arn_type == 'Image':
        return Image(arn) 
    elif arn_type == 'SecurityGroup':
        return SecurityGroup(arn)


def extract_arns(field, value_section):
    if field == 'BlockDeviceMappings':
        volume_ids = list()
        for volume in value_section:
            if 'Ebs' in volume.keys():
                volume_ids.append(volume['Ebs']['VolumeId'])
        return volume_ids
    elif field == 'ImageId':
        return [value_section] 
    elif field == 'SecurityGroups':
        return [group['GroupId'] for group in value_section]
    else:
        return list()


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

        # TODO move this
        if arn in direct_descendants.keys():
            print("Already found ", arn)
            return None
        else:
            direct_descendants[arn] = list()

        self.arn = arn
        self.children = None
        self.tag_str = None
        self.payload = None
        self.ref_time = None
        self.asset_id = None

    def get_asset_id(self):
        asset_type = self._type
        id_field = fuzzy_fields[asset_type]['_id']
        return self.payload[id_field]


class Instance(Asset):
    """

    """
    def __init__(self, arn):
        super().__init__(arn)

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

        self.payload = payload['Reservations'][0]['Instances'][0]


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

        self.payload = payload['Volumes'][0]


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

    assets = {}

    while True:
        if len(arns)==0:
            break;
        else:
            arn = arns.pop()
            this_asset = fetch_asset_obj(arn)
            this_asset.fetch_asset()
            pp(this_asset.payload)
            search_keys = interesting_fields[get_arn_type(arn)]
            keys_found = [k for k in search_keys if k in this_asset.payload.keys()]
            for k in keys_found:
                vs = extract_arns(k, this_asset.payload[k])
                pp(vs)
                 
                [arns.append(v) for v in vs] 
                

    sys.exit()
    for arn in arns:
        print('\n\nFetching {}:'.format(arn))
        this_asset = fetch_asset_obj(arn)
        this_asset.fetch_asset()

        this_asset._type = get_arn_type(arn)
        # this_asset._id = this_asset.get_asset_id()
        assets[arn] = this_asset 
  



     
    pp(assets)
    print(direct_descendants) 
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

