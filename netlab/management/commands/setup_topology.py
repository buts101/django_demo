from django.core.management.base import BaseCommand
from netlab.models import (
    Router, NetworkInterface, NetworkTopology, TopologyRouter, 
    NetworkLink, OSPFConfiguration, MPLSConfiguration
)


class Command(BaseCommand):
    help = 'Setup a sample 4-router MPLS OSPF network topology for testing'

    def handle(self, *args, **options):
        self.stdout.write('Setting up 4-router MPLS OSPF topology...')
        
        # Create routers
        routers = []
        router_configs = [
            {
                'name': 'R1-PE',
                'router_type': 'PE',
                'ip_address': '192.168.1.1',
                'loopback_ip': '10.1.1.1',
                'as_number': 65001,
                'position': (100, 100)
            },
            {
                'name': 'R2-P',
                'router_type': 'P',
                'ip_address': '192.168.1.2',
                'loopback_ip': '10.1.1.2',
                'as_number': 65001,
                'position': (300, 100)
            },
            {
                'name': 'R3-P',
                'router_type': 'P',
                'ip_address': '192.168.1.3',
                'loopback_ip': '10.1.1.3',
                'as_number': 65001,
                'position': (300, 300)
            },
            {
                'name': 'R4-PE',
                'router_type': 'PE',
                'ip_address': '192.168.1.4',
                'loopback_ip': '10.1.1.4',
                'as_number': 65001,
                'position': (100, 300)
            }
        ]
        
        for config in router_configs:
            router, created = Router.objects.get_or_create(
                name=config['name'],
                defaults={
                    'router_type': config['router_type'],
                    'ip_address': config['ip_address'],
                    'loopback_ip': config['loopback_ip'],
                    'as_number': config['as_number'],
                    'mpls_enabled': True,
                    'ospf_enabled': True,
                }
            )
            routers.append((router, config['position']))
            if created:
                self.stdout.write(f'Created router: {router.name}')
            else:
                self.stdout.write(f'Router already exists: {router.name}')
        
        # Create topology
        topology, created = NetworkTopology.objects.get_or_create(
            name='4-Router MPLS OSPF Lab',
            defaults={
                'description': 'Test topology with 4 routers configured for MPLS and OSPF protocols',
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(f'Created topology: {topology.name}')
        else:
            self.stdout.write(f'Topology already exists: {topology.name}')
        
        # Add routers to topology
        for router, position in routers:
            topology_router, created = TopologyRouter.objects.get_or_create(
                topology=topology,
                router=router,
                defaults={
                    'position_x': position[0],
                    'position_y': position[1],
                }
            )
        
        # Create interfaces for each router
        interface_configs = [
            # R1-PE interfaces
            {'router': 'R1-PE', 'name': 'GigabitEthernet0/0', 'ip': '192.168.12.1', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R1-PE', 'name': 'GigabitEthernet0/1', 'ip': '192.168.14.1', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R1-PE', 'name': 'Loopback0', 'ip': '10.1.1.1', 'mask': '255.255.255.255', 'area': '0.0.0.0'},
            
            # R2-P interfaces
            {'router': 'R2-P', 'name': 'GigabitEthernet0/0', 'ip': '192.168.12.2', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R2-P', 'name': 'GigabitEthernet0/1', 'ip': '192.168.23.2', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R2-P', 'name': 'Loopback0', 'ip': '10.1.1.2', 'mask': '255.255.255.255', 'area': '0.0.0.0'},
            
            # R3-P interfaces
            {'router': 'R3-P', 'name': 'GigabitEthernet0/0', 'ip': '192.168.23.3', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R3-P', 'name': 'GigabitEthernet0/1', 'ip': '192.168.34.3', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R3-P', 'name': 'Loopback0', 'ip': '10.1.1.3', 'mask': '255.255.255.255', 'area': '0.0.0.0'},
            
            # R4-PE interfaces
            {'router': 'R4-PE', 'name': 'GigabitEthernet0/0', 'ip': '192.168.14.4', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R4-PE', 'name': 'GigabitEthernet0/1', 'ip': '192.168.34.4', 'mask': '255.255.255.0', 'area': '0.0.0.0'},
            {'router': 'R4-PE', 'name': 'Loopback0', 'ip': '10.1.1.4', 'mask': '255.255.255.255', 'area': '0.0.0.0'},
        ]
        
        for config in interface_configs:
            router = Router.objects.get(name=config['router'])
            interface, created = NetworkInterface.objects.get_or_create(
                router=router,
                interface_name=config['name'],
                defaults={
                    'ip_address': config['ip'],
                    'subnet_mask': config['mask'],
                    'ospf_area': config['area'],
                }
            )
            if created:
                self.stdout.write(f'Created interface: {router.name} - {interface.interface_name}')
        
        # Create network links
        link_configs = [
            # R1 - R2 link
            {
                'router_a': 'R1-PE', 'interface_a': 'GigabitEthernet0/0',
                'router_b': 'R2-P', 'interface_b': 'GigabitEthernet0/0',
                'bandwidth': 1000
            },
            # R2 - R3 link
            {
                'router_a': 'R2-P', 'interface_a': 'GigabitEthernet0/1',
                'router_b': 'R3-P', 'interface_b': 'GigabitEthernet0/0',
                'bandwidth': 1000
            },
            # R3 - R4 link
            {
                'router_a': 'R3-P', 'interface_a': 'GigabitEthernet0/1',
                'router_b': 'R4-PE', 'interface_b': 'GigabitEthernet0/1',
                'bandwidth': 1000
            },
            # R4 - R1 link
            {
                'router_a': 'R4-PE', 'interface_a': 'GigabitEthernet0/0',
                'router_b': 'R1-PE', 'interface_b': 'GigabitEthernet0/1',
                'bandwidth': 1000
            },
        ]
        
        for config in link_configs:
            router_a = Router.objects.get(name=config['router_a'])
            router_b = Router.objects.get(name=config['router_b'])
            interface_a = NetworkInterface.objects.get(router=router_a, interface_name=config['interface_a'])
            interface_b = NetworkInterface.objects.get(router=router_b, interface_name=config['interface_b'])
            
            link, created = NetworkLink.objects.get_or_create(
                topology=topology,
                router_a=router_a,
                router_b=router_b,
                defaults={
                    'interface_a': interface_a,
                    'interface_b': interface_b,
                    'bandwidth': config['bandwidth'],
                }
            )
            if created:
                self.stdout.write(f'Created link: {router_a.name} <-> {router_b.name}')
        
        # Create OSPF configurations
        for router, _ in routers:
            ospf_config, created = OSPFConfiguration.objects.get_or_create(
                router=router,
                defaults={
                    'process_id': 1,
                    'ospf_router_id': router.loopback_ip,
                    'area': '0.0.0.0',
                    'network_statements': '["192.168.0.0/16", "10.1.1.0/24"]'
                }
            )
            if created:
                self.stdout.write(f'Created OSPF config for: {router.name}')
        
        # Create MPLS configurations
        for router, _ in routers:
            mpls_config, created = MPLSConfiguration.objects.get_or_create(
                router=router,
                defaults={
                    'ldp_router_id': router.loopback_ip,
                    'label_range_min': 16,
                    'label_range_max': 1048575,
                }
            )
            if created:
                self.stdout.write(f'Created MPLS config for: {router.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully setup 4-router MPLS OSPF topology!')
        )