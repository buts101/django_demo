from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import (
    Router, NetworkInterface, NetworkTopology, TopologyRouter,
    NetworkLink, OSPFConfiguration, MPLSConfiguration, NetworkTest
)


class NetlabModelsTest(TestCase):
    """Test cases for netlab models"""
    
    def setUp(self):
        """Set up test data"""
        self.router = Router.objects.create(
            name='Test-Router',
            router_type='PE',
            ip_address='192.168.1.1',
            loopback_ip='10.1.1.1',
            as_number=65001,
            mpls_enabled=True,
            ospf_enabled=True
        )
        
        self.topology = NetworkTopology.objects.create(
            name='Test Topology',
            description='Test topology for unit tests',
            is_active=True
        )
    
    def test_router_creation(self):
        """Test router model creation"""
        self.assertEqual(self.router.name, 'Test-Router')
        self.assertEqual(self.router.router_type, 'PE')
        self.assertTrue(self.router.mpls_enabled)
        self.assertTrue(self.router.ospf_enabled)
        self.assertEqual(str(self.router), 'Test-Router (PE)')
    
    def test_network_interface_creation(self):
        """Test network interface creation"""
        interface = NetworkInterface.objects.create(
            router=self.router,
            interface_name='GigabitEthernet0/0',
            ip_address='192.168.1.1',
            subnet_mask='255.255.255.0',
            ospf_area='0.0.0.0'
        )
        self.assertEqual(interface.router, self.router)
        self.assertEqual(interface.interface_name, 'GigabitEthernet0/0')
        self.assertEqual(str(interface), 'Test-Router - GigabitEthernet0/0')
    
    def test_topology_creation(self):
        """Test network topology creation"""
        self.assertEqual(self.topology.name, 'Test Topology')
        self.assertTrue(self.topology.is_active)
        self.assertEqual(self.topology.get_router_count(), 0)
    
    def test_ospf_configuration(self):
        """Test OSPF configuration"""
        ospf_config = OSPFConfiguration.objects.create(
            router=self.router,
            process_id=1,
            ospf_router_id='10.1.1.1',
            area='0.0.0.0',
            network_statements='["192.168.1.0/24"]'
        )
        self.assertEqual(ospf_config.router, self.router)
        self.assertEqual(ospf_config.ospf_router_id, '10.1.1.1')
        self.assertEqual(ospf_config.get_networks(), ["192.168.1.0/24"])
    
    def test_mpls_configuration(self):
        """Test MPLS configuration"""
        mpls_config = MPLSConfiguration.objects.create(
            router=self.router,
            ldp_router_id='10.1.1.1',
            label_range_min=16,
            label_range_max=1048575
        )
        self.assertEqual(mpls_config.router, self.router)
        self.assertEqual(mpls_config.ldp_router_id, '10.1.1.1')


class NetlabViewsTest(TestCase):
    """Test cases for netlab views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test routers
        self.router1 = Router.objects.create(
            name='R1-PE',
            router_type='PE',
            ip_address='192.168.1.1',
            loopback_ip='10.1.1.1',
            as_number=65001,
            mpls_enabled=True,
            ospf_enabled=True
        )
        
        self.router2 = Router.objects.create(
            name='R2-P',
            router_type='P',
            ip_address='192.168.1.2',
            loopback_ip='10.1.1.2',
            as_number=65001,
            mpls_enabled=True,
            ospf_enabled=True
        )
        
        # Create test topology
        self.topology = NetworkTopology.objects.create(
            name='Test Topology',
            description='Test topology for unit tests',
            is_active=True
        )
        
        # Add routers to topology
        TopologyRouter.objects.create(
            topology=self.topology,
            router=self.router1,
            position_x=100,
            position_y=100
        )
        
        TopologyRouter.objects.create(
            topology=self.topology,
            router=self.router2,
            position_x=200,
            position_y=100
        )
    
    def test_index_view(self):
        """Test the main index view"""
        response = self.client.get(reverse('netlab:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'NetLab - MPLS OSPF Testing Environment')
        self.assertContains(response, 'Test Topology')
    
    def test_topology_detail_view(self):
        """Test topology detail view"""
        response = self.client.get(reverse('netlab:topology_detail', args=[self.topology.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Topology')
        self.assertContains(response, 'R1-PE')
        self.assertContains(response, 'R2-P')
    
    def test_router_detail_view(self):
        """Test router detail view"""
        response = self.client.get(reverse('netlab:router_detail', args=[self.router1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'R1-PE')
        self.assertContains(response, 'Provider Edge')
    
    def test_run_test_view(self):
        """Test running a network test"""
        response = self.client.post(reverse('netlab:run_test'), {
            'test_type': 'ping',
            'source_router': self.router1.id,
            'target_router': self.router2.id,
            'topology': self.topology.id
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful test
        
        # Check that test was created
        test = NetworkTest.objects.filter(
            test_type='ping',
            source_router=self.router1,
            target_router=self.router2
        ).first()
        self.assertIsNotNone(test)
        self.assertEqual(test.status, 'completed')
        self.assertTrue(test.success)
    
    def test_topology_json_view(self):
        """Test topology JSON API"""
        response = self.client.get(reverse('netlab:topology_json', args=[self.topology.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        import json
        data = json.loads(response.content)
        self.assertIn('nodes', data)
        self.assertIn('edges', data)
        self.assertEqual(len(data['nodes']), 2)


class NetworkTestingTest(TestCase):
    """Test cases for network testing functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.router = Router.objects.create(
            name='Test-Router',
            router_type='PE',
            ip_address='192.168.1.1',
            loopback_ip='10.1.1.1',
            as_number=65001,
            mpls_enabled=True,
            ospf_enabled=True
        )
        
        self.topology = NetworkTopology.objects.create(
            name='Test Topology',
            description='Test topology',
            is_active=True
        )
    
    def test_ping_test_simulation(self):
        """Test ping test simulation"""
        from .views import simulate_network_test
        
        test = NetworkTest.objects.create(
            topology=self.topology,
            test_type='ping',
            source_router=self.router,
            target_router=self.router,  # Self-ping for testing
            status='running'
        )
        
        result = simulate_network_test(test)
        self.assertTrue(result['success'])
        self.assertIn('PING', result['output'])
        self.assertIn('packet loss', result['output'])
    
    def test_ospf_neighbors_test_simulation(self):
        """Test OSPF neighbors test simulation"""
        from .views import simulate_network_test
        
        test = NetworkTest.objects.create(
            topology=self.topology,
            test_type='ospf_neighbors',
            source_router=self.router,
            status='running'
        )
        
        result = simulate_network_test(test)
        self.assertTrue(result['success'])
        self.assertIn('OSPF Neighbor Table', result['output'])
        self.assertIn('Neighbor ID', result['output'])
    
    def test_mpls_labels_test_simulation(self):
        """Test MPLS labels test simulation"""
        from .views import simulate_network_test
        
        test = NetworkTest.objects.create(
            topology=self.topology,
            test_type='mpls_labels',
            source_router=self.router,
            status='running'
        )
        
        result = simulate_network_test(test)
        self.assertTrue(result['success'])
        self.assertIn('MPLS Label Table', result['output'])
        self.assertIn('Local', result['output'])
        self.assertIn('Outgoing', result['output'])
