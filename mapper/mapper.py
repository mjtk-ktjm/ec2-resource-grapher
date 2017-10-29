import boto3
from graphviz import Digraph
import re
from pprint import pprint as pp
import sys

resources_found = list()
resource_tree = dict()
direct_descendants = dict()

interesting_fields = {'Instance':['BlockDeviceMappings','ImageId','SecurityGroups'],
                    'Volume':['SnapshotId',],
                    'Snapshot':[],
                    'Image':[],
                    'SecurityGroup':[],
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


def get_payload_obj(arn):
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
    elif field == 'SnapshotId':
        return [value_section]
    elif field == 'SecurityGroups':
        return [group['GroupId'] for group in value_section]
    else:
        return list()


def build_viz(node):
    branch = { node.arn : [] }
    try:
        tag_str = node.tag_str
    except:
        tag_str = 'N/A'
    graph_out.node(node.arn, node.arn+'\n\n'+tag_str)
    children = list(node.children.keys())
    if len(children)>0:
        for child in children:
            child_asset = build_viz(node.children[child])
            branch[node.arn].append(child_asset)
            graph_out.edge(node.children[child].arn, node.arn)
    return branch


def build_resource_tree(node):
    """
    args:
        root_arn : amazon resource name as the root of the resource tree
    returns:
        resource_tree : nested dicitonaries from root to leaf nodes plus metadata
    """
    children = node.find_children()
    if len(children) == 0:
        return node
    for child in children:
        child_node = build_resource_tree(get_payload_obj(child))
        node.children[child] = child_node
    return node


class ZeroReservationError(TypeError):
    pass


class Asset:
    """
    Base Class for amazon assets.
    """
    def __init__(self, arn):

        # TODO move this
        if arn in resources_found:
            print("Already found ", arn)
            return None
        else:
            resources_found.append(arn)

        self.arn = arn
        self.children = dict() 

        self.ref_time = None

    def get_asset_id(self):
        asset_type = self._type
        id_field = fuzzy_fields[asset_type]['_id']
        return self.payload[id_field]

    def find_children(self):
        child_arns = list()
        search_keys = interesting_fields[self._type]
        keys_found = [k for k in search_keys if k in self.payload.keys()]
        for k in keys_found:
            vs = extract_arns(k, self.payload[k])
            child_arns += vs
        return child_arns 

    def add_tag_str(self):
        if 'Tags' not in self.payload.keys(): 
            return ''
        tags = self.payload['Tags']
        if tags is None or len(tags) == 0:
            return ''
        tag_list = [list(x) for x in [y.values() for y in tags]]
        formatted_tags = [str(val[0])+'='+str(val[1]) for val in tag_list]
        self.tag_str = '\n'.join(formatted_tags)


class Instance(Asset):
    """

    """
    def __init__(self, arn):
        super().__init__(arn)
        self._type = "Instance"
        self.get_payload()
        self.add_tag_str() 

    def get_payload(self):
        try:
            payload = ec2.describe_instances(InstanceIds=[self.arn])
        except:
            print('Instance does not exist.')
            return None
        
        if 'Reservations' not in payload.keys() or len(payload['Reservations'])==0:
            print('Zero reservations.')
            # raise ZeroReservationError('No reservations found in {} payload.'.format(arn))
            return None

        if len(payload['Reservations'])>1:
            print('More than 1 reservation here!')

        if len(payload['Reservations'][0]['Instances'])>1:
            print('More than 1 instance here!')

        self.payload = payload['Reservations'][0]['Instances'][0]


class Volume(Asset):
    """

    """
    def __init__(self, arn):
        super().__init__(arn)
        self._type = "Volume"
        self.get_payload()
        self.add_tag_str() 

    def get_payload(self):
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
    def __init__(self, arn):
        super().__init__(arn)
        self._type = "Snapshot"
        self.get_payload()
        self.add_tag_str() 

    def get_payload(self):
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
    def __init__(self, arn):
        super().__init__(arn)
        self._type = "Image"
        self.get_payload()
        self.add_tag_str() 

    def get_payload(self):
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
    def __init__(self, arn):
        super().__init__(arn)
        self._type = "SecurityGroup"
        self.get_payload()
        self.add_tag_str() 

    def get_payload(self):
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
    root_arn = 'i-836b9d9b'

    this_asset = get_payload_obj(root_arn)
    resource_tree = build_resource_tree(this_asset)

    # pp(resource_tree.children['vol-596aeefe'].tag_str)
    # pp(resource_tree.tag_str)
    graph_out = Digraph('test', filename='test.gv')
    build_viz(resource_tree)
    graph_out.view()

